"""Pruebas del consumo, validación y guardado de indicadores financieros."""
import unittest
from datetime import date
from unittest.mock import patch

from src.dependencia.indicador import Indicador
from src.indicadores import ErrorAPI, crear_indicador, obtener_datos
from src.persistencia import IndicadorDAO
from src.servicios.indicadores import consultar_historial, consultar_indicador
from tests.apoyo import BaseBD


def respuesta(codigo="dolar", valor=950.5):
    return {
        "result": "success",
        "base_code": {"dolar": "USD", "euro": "EUR"}[codigo],
        "time_last_update_unix": 1793836800,  # 2026-11-05
        "rates": {"CLP": valor},
    }


class ConsumoAPIIndicadoresTest(unittest.TestCase):
    def test_solo_permite_indicadores_conocidos(self):
        with self.assertRaises(ValueError):
            obtener_datos("acciones")

    def test_crea_objeto_validado(self):
        indicador = crear_indicador(respuesta(), "dolar")
        self.assertEqual(indicador.codigo, "dolar")
        self.assertEqual(indicador.fecha, date(2026, 11, 5))
        self.assertEqual(indicador.valor, 950.5)
        self.assertEqual(indicador.unidad, "Pesos")

    def test_respuesta_de_otro_indicador_se_rechaza(self):
        with self.assertRaises(ValueError):
            crear_indicador(respuesta("euro"), "dolar")

    def test_http_429_se_informa_sin_detalles_tecnicos(self):
        import requests
        from unittest.mock import Mock

        respuesta_http = Mock()
        respuesta_http.status_code = 429
        respuesta_http.raise_for_status.side_effect = requests.HTTPError("Too Many Requests")
        with patch("src.indicadores.requests.get", return_value=respuesta_http):
            with self.assertRaisesRegex(ErrorAPI, "demasiadas consultas"):
                obtener_datos("dolar")
        respuesta_http.json.assert_not_called()


class PersistenciaIndicadoresTest(BaseBD):
    def test_consulta_guarda_el_valor_y_muestra_historial(self):
        sesion = self.sesion()
        with patch("src.servicios.indicadores.obtener_datos", return_value=respuesta()):
            indicador, origen, mensaje = consultar_indicador(sesion, "dolar")

        self.assertEqual(indicador.valor, 950.5)
        historial = consultar_historial(sesion, "dolar")
        self.assertEqual(len(historial), 1)
        self.assertEqual(historial[0].fecha, date(2026, 11, 5))
        self.assertEqual(historial[0].valor, 950.5)

    def test_actualiza_un_registro_de_la_misma_fecha(self):
        primero = Indicador("dolar", date(2026, 11, 5), 950.0)
        segundo = Indicador("dolar", date(2026, 11, 5), 955.0)
        IndicadorDAO.guardar(primero)
        IndicadorDAO.guardar(segundo)
        historial = IndicadorDAO.listar_historial("dolar")
        self.assertEqual(len(historial), 1)
        self.assertEqual(historial[0].valor, 955.0)

    def test_no_consulta_api_sin_sesion(self):
        with patch("src.servicios.indicadores.obtener_datos") as consultar:
            with self.assertRaises(PermissionError):
                consultar_indicador(None, "dolar")
        consultar.assert_not_called()

    def test_historial_rechaza_limite_invalido(self):
        with self.assertRaises(ValueError):
            IndicadorDAO.listar_historial("dolar", 1000)


class RespaldoIndicadoresTest(BaseBD):
    def setUp(self):
        super().setUp()
        self.sesion_actual = self.sesion()

    def guardar(self):
        with patch("src.servicios.indicadores.obtener_datos", return_value=respuesta()):
            return consultar_indicador(self.sesion_actual, "dolar")[0]

    def test_fallo_api_recupera_sin_cambiar_verificacion(self):
        original = self.guardar()
        for error in (ErrorAPI("Sin conexión"), ValueError("JSON inválido")):
            with patch("src.servicios.indicadores.obtener_datos", side_effect=error):
                dato, origen, mensaje = consultar_indicador(self.sesion_actual, "dolar")
            self.assertEqual(origen, "BD")
            self.assertEqual(dato.fecha, original.fecha)
            self.assertEqual(dato.verificado_en, original.verificado_en.replace(microsecond=0))
            self.assertIn("no es una consulta nueva", mensaje)

    def test_sin_respaldo_no_inventa(self):
        with patch("src.servicios.indicadores.obtener_datos", side_effect=ErrorAPI("Sin conexión")):
            dato, _, mensaje = consultar_indicador(self.sesion_actual, "euro")
        self.assertIsNone(dato)
        self.assertIn("No hay", mensaje)

    def test_filtro_por_fuente_y_codigo(self):
        IndicadorDAO.guardar(Indicador("dolar", date(2026, 11, 5), 999, fuente="otra_api"))
        IndicadorDAO.guardar(Indicador("euro", date(2026, 11, 5), 1000))
        self.assertEqual(consultar_historial(self.sesion_actual, "dolar"), [])

    def test_filtro_por_unidad_en_datos_anteriores(self):
        from src.persistencia.dao_util import sesion_bd
        self.guardar()
        with sesion_bd() as cursor:
            cursor.execute("UPDATE indicador_api SET unidad = ?", ("Otra unidad",))
        self.assertEqual(consultar_historial(self.sesion_actual, "dolar"), [])

    def test_error_guardado_conserva_valor_api(self):
        from src.persistencia import DAOError
        with patch("src.servicios.indicadores.obtener_datos", return_value=respuesta()), patch.object(IndicadorDAO, "guardar_varios", side_effect=DAOError("Fallo")):
            dato, origen, mensaje = consultar_indicador(self.sesion_actual, "dolar")
        self.assertEqual(dato.valor, 950.5)
        self.assertEqual(origen, "API")
        self.assertIn("no se pudo guardar", mensaje)

    def test_historial_no_consulta_http_y_sobrevive_reapertura(self):
        from src.persistencia import crear_tablas
        self.guardar()
        crear_tablas()
        with patch("src.servicios.indicadores.obtener_datos") as api:
            self.assertEqual(len(consultar_historial(self.sesion_actual, "dolar")), 1)
        api.assert_not_called()

    def test_monto_limites_y_decimal(self):
        from decimal import Decimal
        from src.servicios.indicadores import validar_monto, convertir_monto
        for monto in ("-1", "NaN", "inf", "1e308", "1000000001", "1.234", "", "1 000", "1.000,50"):
            with self.subTest(monto=monto), self.assertRaises(ValueError):
                validar_monto(monto)
        self.assertEqual(validar_monto("1000,50"), Decimal("1000.50"))
        dato = Indicador("dolar", date(2026, 11, 5), 900)
        self.assertEqual(convertir_monto(self.sesion_actual, "1000", dato), Decimal("1.1111"))
        with self.assertRaises(PermissionError):
            convertir_monto(None, "1000", dato)

    def test_pantalla_api_no_afirma_guardado_si_falla(self):
        import io
        from src.menus.menu_indicadores import _consultar
        from src.persistencia import DAOError
        with patch("src.servicios.indicadores.obtener_datos", return_value=respuesta()), patch.object(IndicadorDAO, "guardar_varios", side_effect=DAOError("Fallo")), patch("builtins.input", return_value="n"), patch("sys.stdout", new_callable=io.StringIO) as salida:
            _consultar(self.sesion_actual, "dolar")
        texto = salida.getvalue()
        self.assertIn("950.50", texto)
        self.assertIn("Origen de esta lectura: API", texto)
        self.assertIn("no se pudo guardar", texto)
        self.assertNotIn("quedó guardado", texto)

    def test_pantalla_respaldo_y_conversion(self):
        import io
        from src.menus.menu_indicadores import _consultar
        self.guardar()
        with patch("src.servicios.indicadores.obtener_datos", side_effect=ErrorAPI("Sin conexión")), patch("builtins.input", side_effect=["s", "NaN", "950.50"]), patch("sys.stdout", new_callable=io.StringIO) as salida:
            _consultar(self.sesion_actual, "dolar")
        texto = salida.getvalue()
        self.assertIn("Origen de esta lectura: BD", texto)
        self.assertIn("Última verificación", texto)
        self.assertIn("1.0000 DOLAR", texto)
        self.assertIn("tasa guardada", texto)
