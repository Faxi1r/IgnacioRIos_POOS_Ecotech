import unittest
from unittest.mock import patch, Mock
import requests
from src.dependencia import Empleado
from src.indicadores import obtener_datos, extraer_primero, URL_DOLAR
from src.menus import comunes, menu_indicadores, menu_empleado
from src.persistencia import EmpleadoDAO
from tests.apoyo import BaseBD, empleado


def respuesta_ejemplo():
    return {
        "result": "success",
        "base_code": "USD",
        "time_last_update_unix": 1767312000,  # 2026-01-02
        "rates": {"CLP": 900.0},
    }


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
        for correo in (
            "anaempresa.cl",
            "ana@empresa..cl",
            "ana@.cl",
            "ana@empresa.cl.",
            "ana @empresa.cl",
            "ana@@empresa.cl",
            "@empresa.cl",
        ):
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
        sesion = self.sesion()
        entradas = [
            "EMP0001",
            "Ana Torres",
            "ana@empresa..cl",
            "ana@empresa.cl",
            "900000",
            "Calle 123",
            "+56912345678",
            "2026-01-02",
        ]
        with patch("builtins.input", side_effect=entradas) as leer, patch("builtins.print"):
            menu_empleado.registrar_empleado(sesion)
        self.assertEqual(leer.call_count, 8)
        self.assertEqual(EmpleadoDAO.buscar_por_identificacion("EMP0001").nombre, "Ana Torres")


class IndicadoresU3Test(unittest.TestCase):
    def test_respuesta_correcta(self):
        self.assertEqual(extraer_primero(respuesta_ejemplo()), ("2026-01-02", 900.0))

    def test_sin_tasas_controlado(self):
        datos = respuesta_ejemplo()
        datos["rates"] = {}
        with self.assertRaises(ValueError):
            extraer_primero(datos)

    def test_valores_invalidos(self):
        for valor in (0, -1, True, "900", float("nan"), float("inf"), None, 10**1000):
            datos = respuesta_ejemplo()
            datos["rates"]["CLP"] = valor
            with self.subTest(valor=str(valor)[:20]), self.assertRaises(ValueError):
                extraer_primero(datos)

    def test_resultado_base_fecha_y_estructura(self):
        for clave, valor in (("result", "error"), ("base_code", "EUR"), ("rates", None)):
            datos = respuesta_ejemplo()
            datos[clave] = valor
            with self.subTest(clave=clave), self.assertRaises(ValueError):
                extraer_primero(datos)
        for fecha in (None, "ayer", -5, True):
            datos = respuesta_ejemplo()
            datos["time_last_update_unix"] = fecha
            with self.subTest(fecha=fecha), self.assertRaises(ValueError):
                extraer_primero(datos)
        for datos in ([], None):
            with self.assertRaises(ValueError):
                extraer_primero(datos)

    def test_http_antes_de_json(self):
        respuesta = Mock()
        respuesta.json.return_value = respuesta_ejemplo()
        with patch("src.indicadores.requests.get", return_value=respuesta) as get:
            self.assertEqual(obtener_datos(), respuesta_ejemplo())
        get.assert_called_once_with(URL_DOLAR, timeout=(3, 5))
        self.assertEqual([c[0] for c in respuesta.mock_calls], ["raise_for_status", "json", "close"])

        respuesta.reset_mock()
        respuesta.status_code = 503
        respuesta.raise_for_status.side_effect = requests.HTTPError("Fallo HTTP")
        with patch("src.indicadores.requests.get", return_value=respuesta), self.assertRaises(
            menu_indicadores.ErrorAPI
        ):
            obtener_datos()
        respuesta.json.assert_not_called()

    def test_error_de_red_se_muestra_de_forma_simple(self):
        with patch(
            "src.menus.menu_indicadores.consultar_indicador",
            side_effect=menu_indicadores.ErrorAPI("No hay conexión con el servicio."),
        ), patch("builtins.print") as mostrar:
            menu_indicadores._consultar({}, "dolar")
        self.assertIn("No hay conexión", " ".join(str(c.args[0]) for c in mostrar.call_args_list))


class IntegracionMenuU3Test(BaseBD):
    def test_administrador_abre_menu_indicadores(self):
        from src import main

        sesion = self.sesion(self.cuenta(admin=True))
        with patch("builtins.input", side_effect=["3", "0"]), patch("builtins.print"), patch(
            "src.main.menu_indicadores"
        ) as menu:
            main.menu_principal(sesion)
        menu.assert_called_once_with(sesion)

    def test_empleado_tambien_puede_consultar_indicadores(self):
        from src import main

        sesion = self.sesion(self.cuenta())
        with patch("builtins.input", side_effect=["3", "0"]), patch("builtins.print"), patch(
            "src.main.menu_indicadores"
        ) as menu:
            main.menu_principal(sesion)
        menu.assert_called_once_with(sesion)
