import unittest
from unittest.mock import patch, Mock
import requests
from src.dependencia import Empleado
from src.indicadores import obtener_datos, extraer_primero, URL_DOLAR
from src.menus import comunes, menu_indicadores, menu_empleado
from src.persistencia import EmpleadoDAO
from tests.apoyo import BaseBD, empleado


def respuesta_ejemplo():
    return {"codigo": "dolar", "unidad_medida": "Pesos",
            "serie": [{"fecha": "2026-01-02T00:00:00Z", "valor": 900.0}]}


class ValidacionesU3Test(unittest.TestCase):
    def test_nombre_limpio_y_limites(self):
        self.assertEqual(Empleado.validar_nombre(" Ana Torres "), "Ana Torres")
        self.assertEqual(len(Empleado.validar_nombre("A" * 100)), 100)
        for nombre in ("", "A", "A" * 101):
            with self.subTest(nombre=nombre), self.assertRaises(ValueError):
                Empleado.validar_nombre(nombre)

    def test_tipo_incorrecto(self):
        for validar in (Empleado.validar_nombre, Empleado.validar_correo):
            with self.assertRaises(TypeError):
                validar(None)

    def test_correo(self):
        self.assertEqual(Empleado.validar_correo(" ANA@EMPRESA.CL "), "ana@empresa.cl")
        for correo in ("anaempresa.cl", "ana@empresa..cl", "ana@.cl", "ana@empresa.cl.",
                       "ana @empresa.cl", "ana@@empresa.cl", "@empresa.cl"):
            with self.subTest(correo=correo), self.assertRaises(ValueError):
                Empleado.validar_correo(correo)

    def test_constructor_y_setters(self):
        with self.assertRaises(ValueError):
            empleado(nombre="A")
        persona = empleado()
        with self.assertRaises(ValueError):
            persona.nombre = "A"
        with self.assertRaises(ValueError):
            persona.correo = "ana@empresa..cl"

    def test_reintentos(self):
        with patch("builtins.input", side_effect=["A", " Ana "]), patch("builtins.print"):
            self.assertEqual(comunes.pedir_nombre_empleado(), "Ana")
        with patch("builtins.input", return_value=""):
            self.assertEqual(comunes.pedir_nombre_empleado(opcional=True), "")
        validar = Mock(side_effect=[TypeError("Dato incorrecto"), "Ana"])
        with patch("builtins.input", side_effect=["x", "Ana"]), patch("builtins.print"):
            self.assertEqual(comunes.pedir_con_validacion("Nombre: ", validar), "Ana")


class PersistenciaU3Test(BaseBD):
    def test_correo_254_se_guarda_y_busca(self):
        correo = "a" * 60 + "@" + "b" * 60 + "." + "c" * 60 + "." + "d" * 60 + "." + "e" * 10
        self.assertEqual(len(correo), 254)
        persona = self.persona(correo=correo)
        self.assertEqual(EmpleadoDAO.buscar_por_correo(correo).id_empleado, persona.id_empleado)
        with self.assertRaises(ValueError):
            Empleado.validar_correo(correo + "x")

    def test_correo_invalido_no_repite_nombre(self):
        entradas = ["EMP0001", "Ana Torres", "ana@empresa..cl", "ana@empresa.cl",
                    "900000", "Calle 123", "+56912345678", "2026-01-02"]
        with patch("builtins.input", side_effect=entradas) as leer, patch("builtins.print"):
            menu_empleado.registrar_empleado()
        self.assertEqual(leer.call_count, 8)
        self.assertEqual(EmpleadoDAO.listar()[0].nombre, "Ana Torres")


class IndicadoresU3Test(unittest.TestCase):
    def test_respuesta_correcta(self):
        self.assertEqual(extraer_primero(respuesta_ejemplo()), ("2026-01-02", 900.0))

    def test_serie_vacia_controlada(self):
        datos = respuesta_ejemplo()
        datos["serie"] = []
        with self.assertRaises(ValueError):
            extraer_primero(datos)
        with patch("src.menus.menu_indicadores.obtener_datos", return_value=datos), patch("builtins.print") as mostrar:
            menu_indicadores.consultar_dolar()
        self.assertIn("No hay valores disponibles", mostrar.call_args.args[0])

    def test_valores_invalidos(self):
        for valor in (0, -1, True, "900", float("nan"), float("inf"), None):
            datos = respuesta_ejemplo()
            datos["serie"][0]["valor"] = valor
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                extraer_primero(datos)

    def test_codigo_unidad_fecha_y_estructura(self):
        for clave, valor in (("codigo", "uf"), ("unidad_medida", "Dólar"), ("serie", None)):
            datos = respuesta_ejemplo()
            datos[clave] = valor
            with self.subTest(clave=clave), self.assertRaises(ValueError):
                extraer_primero(datos)
        for fecha in (None, "ayer", "2026-02-30"):
            datos = respuesta_ejemplo()
            datos["serie"][0]["fecha"] = fecha
            with self.subTest(fecha=fecha), self.assertRaises(ValueError):
                extraer_primero(datos)
        for datos in ([], {"codigo": "dolar", "unidad_medida": "Pesos", "serie": [None]}):
            with self.assertRaises(ValueError):
                extraer_primero(datos)

    def test_http_antes_de_json(self):
        respuesta = Mock()
        respuesta.json.return_value = respuesta_ejemplo()
        with patch("src.indicadores.requests.get", return_value=respuesta) as get:
            self.assertEqual(obtener_datos(), respuesta_ejemplo())
        get.assert_called_once_with(URL_DOLAR, timeout=(3, 5))
        self.assertEqual([c[0] for c in respuesta.mock_calls], ["raise_for_status", "json"])
        respuesta.reset_mock()
        respuesta.raise_for_status.side_effect = requests.HTTPError("Fallo HTTP")
        with patch("src.indicadores.requests.get", return_value=respuesta), self.assertRaises(requests.HTTPError):
            obtener_datos()
        respuesta.json.assert_not_called()

    def test_errores_de_red_y_json_controlados(self):
        errores = [requests.Timeout(), requests.exceptions.JSONDecodeError("JSON inválido", "x", 0)]
        for error in errores:
            with patch("src.menus.menu_indicadores.obtener_datos", side_effect=error), patch("builtins.print") as mostrar:
                menu_indicadores.consultar_dolar()
            self.assertIn("No pudimos consultar", mostrar.call_args.args[0])

    def test_salida_con_contexto(self):
        with patch("src.menus.menu_indicadores.obtener_datos", return_value=respuesta_ejemplo()), patch("builtins.print") as mostrar:
            menu_indicadores.consultar_dolar()
        texto = " ".join(c.args[0] for c in mostrar.call_args_list)
        for dato in ("900.00 CLP por USD", "2026-01-02", URL_DOLAR):
            self.assertIn(dato, texto)


class IntegracionMenuU3Test(BaseBD):
    def test_editar_nombre_reintenta(self):
        persona = self.persona()
        respuestas = [str(persona.id_empleado), "n", "A", "Ana Nueva", "", "n", "n", "n", "n"]
        with patch("builtins.input", side_effect=respuestas), patch("builtins.print"):
            menu_empleado.actualizar_empleado()
        self.assertEqual(EmpleadoDAO.buscar_por_id(persona.id_empleado).nombre, "Ana Nueva")

    def test_administrador_consulta_desde_opcion_siete(self):
        from src import main
        cuenta = self.cuenta(admin=True)
        with patch("builtins.input", side_effect=["7", "0"]), patch("builtins.print"), patch("src.main.consultar_dolar") as consultar:
            main.menu_principal(cuenta)
        consultar.assert_called_once_with()

    def test_usuario_comun_no_abre_consulta_administrativa(self):
        from src import main
        cuenta = self.cuenta()
        with patch("src.main.menu_personal") as personal, patch("src.main.consultar_dolar") as consultar:
            main.menu_principal(cuenta)
        personal.assert_called_once_with(cuenta)
        consultar.assert_not_called()
