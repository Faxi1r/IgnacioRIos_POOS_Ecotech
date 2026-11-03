import io
from datetime import date
from unittest.mock import patch

from src.menus import comunes, menu_empleado
from src.persistencia import EmpleadoDAO
from tests.apoyo import BaseBD


class MenusTest(BaseBD):
    def test_formulario_registra_y_muestra_confirmacion(self):
        sesion = self.sesion()
        respuestas = [
            "EMP0001",
            "Ana Torres",
            "ana@ejemplo.cl",
            "900000",
            "Calle de Prueba 10",
            "+56 912345678",
            "2026-03-01",
        ]
        salida = io.StringIO()
        with patch("builtins.input", side_effect=respuestas), patch("sys.stdout", salida):
            menu_empleado.registrar_empleado(sesion)
        persona = EmpleadoDAO.buscar_por_identificacion("EMP0001")
        self.assertEqual(persona.nombre, "Ana Torres")
        self.assertEqual(persona.fecha_inicio_contrato, date(2026, 3, 1))
        self.assertIn("registrado correctamente", salida.getvalue())

    def test_reintentos_conservan_los_campos_ya_ingresados(self):
        sesion = self.sesion()
        respuestas = [
            "EMP0001",
            "",
            "Ana Torres",
            "correo_malo",
            "ana@ejemplo.cl",
            "-1",
            "900000",
            "Calle 10",
            "letras",
            "912345678",
            "2026-02-30",
            "2026-03-01",
        ]
        with patch("builtins.input", side_effect=respuestas), patch("sys.stdout", io.StringIO()):
            menu_empleado.registrar_empleado(sesion)
        persona = EmpleadoDAO.buscar_por_identificacion("EMP0001")
        self.assertEqual(persona.nombre, "Ana Torres")
        self.assertEqual(persona.salario, 900000)

    def test_cancelar_formulario_no_guarda_una_ficha_incompleta(self):
        sesion = self.sesion()
        with patch("builtins.input", side_effect=["EMP0001", KeyboardInterrupt]), patch(
            "sys.stdout", io.StringIO()
        ):
            comunes.ejecutar(lambda: menu_empleado.registrar_empleado(sesion))
        self.assertIsNone(EmpleadoDAO.buscar_por_identificacion("EMP0001"))

    def test_correo_duplicado_se_corrige_sin_reiniciar_formulario(self):
        self.persona()
        with patch(
            "builtins.input", side_effect=["persona1@ejemplo.cl", "nuevo@ejemplo.cl"]
        ), patch("sys.stdout", io.StringIO()):
            self.assertEqual(comunes.pedir_correo_nuevo(), "nuevo@ejemplo.cl")

    def test_fecha_exige_formato_completo_y_dia_real(self):
        with patch("builtins.input", side_effect=["2026-2-3", "2026-02-30", "2026-02-03"]), patch(
            "sys.stdout", io.StringIO()
        ):
            self.assertEqual(comunes.pedir_fecha("Fecha: "), date(2026, 2, 3))

    def test_confirmacion_e_id_invalidos_se_preguntan_de_nuevo(self):
        with patch("builtins.input", side_effect=["quizás", "s"]), patch(
            "sys.stdout", io.StringIO()
        ):
            self.assertTrue(comunes.confirmar("Continuar"))
        with patch("builtins.input", side_effect=["0", "1.5", "letras", "3"]), patch(
            "sys.stdout", io.StringIO()
        ):
            self.assertEqual(comunes.pedir_entero("Id: "), 3)

    def test_decimales_con_coma_se_aceptan_sin_aceptar_infinito(self):
        with patch("builtins.input", side_effect=["nan", "inf", "2,5"]), patch(
            "sys.stdout", io.StringIO()
        ):
            self.assertEqual(comunes.pedir_numero("Horas: ", "Las horas", minimo=0, maximo=24), 2.5)

    def test_exportacion_se_queda_en_reportes_con_extension_correcta(self):
        for nombre in ("../../informe", "/tmp/informe", "..", "mi informe"):
            if nombre == "..":
                with self.assertRaises(ValueError):
                    comunes.ruta_exportacion(nombre, ".pdf")
                continue
            for extension in (".pdf", ".xlsx"):
                ruta = comunes.ruta_exportacion(nombre, extension)
                self.assertEqual(ruta.parent, comunes.RAIZ_PROYECTO / "reportes")
                self.assertEqual(ruta.suffix, extension)
