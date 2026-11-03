import inspect
import unittest
from datetime import date

from src.dependencia import (
    Administrador,
    Departamento,
    Empleado,
    Informe,
    Proyecto,
    RegistroDeTiempo,
    Seguridad,
    Usuario,
)
from tests.apoyo import empleado


class ModeloTest(unittest.TestCase):
    def test_solo_administrador_hereda_de_usuario(self):
        self.assertTrue(issubclass(Administrador, Usuario))
        self.assertFalse(issubclass(Empleado, Usuario))
        self.assertFalse(hasattr(empleado(), "cargo"))
        self.assertIsNone(empleado().usuario)

    def test_operaciones_publicas_corresponden_al_uml(self):
        esperadas = {
            Usuario: {
                "establecer_contrasena",
                "autenticar",
                "puede_acceder",
                "desactivar",
                "validar_rol",
            },
            Administrador: {"puede_acceder", "generar_informe"},
            Empleado: {"validar_datos", "registrar_horas", "validar_nombre", "validar_correo"},
            Departamento: {
                "validar_datos",
                "agregar_empleado",
                "quitar_empleado",
                "asignar_gerente",
            },
            Proyecto: {"validar_datos", "asignar_empleado", "desasignar_empleado"},
            RegistroDeTiempo: {"validar_datos"},
            Informe: {"generar", "exportar_pdf", "exportar_excel"},
            Seguridad: {"hashear_contrasena", "verificar_contrasena", "cifrar", "descifrar"},
        }
        for clase, nombres in esperadas.items():
            with self.subTest(clase=clase.__name__):
                reales = {
                    n
                    for n, valor in vars(clase).items()
                    if not n.startswith("_")
                    and (inspect.isfunction(valor) or isinstance(valor, classmethod))
                }
                self.assertEqual(reales, nombres)

    def test_registrar_horas_recibe_la_fecha_como_en_el_uml(self):
        self.assertEqual(
            list(inspect.signature(Empleado.registrar_horas).parameters),
            ["self", "fecha", "proyecto", "horas", "descripcion"],
        )

    def test_permisos_cambian_segun_el_tipo_de_cuenta(self):
        cuentas = [Usuario(None, "normal"), Administrador(None, "admin")]
        self.assertEqual([u.puede_acceder("informes") for u in cuentas], [False, True])
        self.assertTrue(all(u.puede_acceder("mi_cuenta") for u in cuentas))
        self.assertFalse(cuentas[1].puede_acceder("modulo_inexistente"))

    def test_desactivar_quita_los_permisos_y_el_acceso(self):
        for clase in (Usuario, Administrador):
            with self.subTest(clase=clase.__name__):
                cuenta = clase(None, "prueba")
                cuenta.establecer_contrasena("Prueba2026*")
                cuenta.desactivar()
                self.assertFalse(cuenta.autenticar("Prueba2026*"))
                self.assertFalse(cuenta.puede_acceder("mi_cuenta"))
                with self.assertRaises(AttributeError):
                    cuenta.activo = True

    def test_datos_personales_se_validan_al_modificarlos(self):
        persona = empleado()
        for campo, valor in [
            ("nombre", ""),
            ("correo", "sin-arroba"),
            ("direccion", ""),
            ("telefono", ""),
            ("telefono", "abcdef"),
            ("fecha_inicio_contrato", None),
        ]:
            with self.subTest(campo=campo), self.assertRaises(ValueError):
                setattr(persona, campo, valor)

    def test_salario_rechaza_valores_imposibles(self):
        for valor in (-1, True, "nan", "inf", 0.001, 10000000000):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                empleado(salario=valor)
        self.assertEqual(empleado(salario=0).salario, 0)

    def test_identificacion_y_correo_se_normalizan(self):
        persona = empleado(identificacion="emp-00.01", correo=" ANA@EJEMPLO.CL ")
        self.assertEqual(persona.identificacion, "EMP0001")
        self.assertEqual(persona.correo, "ana@ejemplo.cl")

    def test_personas_nuevas_son_distintas_y_guardadas_se_comparan_por_id(self):
        self.assertNotEqual(empleado(), empleado())
        self.assertEqual(empleado(id_empleado=7), empleado(2, id_empleado=7))

    def test_departamento_necesita_gerente_y_lo_incluye(self):
        persona = empleado()
        departamento = Departamento(None, "Tecnología", persona)
        self.assertEqual(departamento.empleados, [persona])
        self.assertIs(persona.departamento, departamento)
        with self.assertRaises(ValueError):
            Departamento(None, "Sin gerente", None)

    def test_un_departamento_invalido_no_se_apropia_de_empleados(self):
        persona = empleado()
        with self.assertRaises(ValueError):
            Departamento(None, "Inválido", None, [persona])
        self.assertIsNone(persona.departamento)

    def test_gerente_se_reemplaza_antes_de_quitarlo(self):
        ana, luis = empleado(), empleado(2)
        departamento = Departamento(None, "Tecnología", ana)
        with self.assertRaises(ValueError):
            departamento.quitar_empleado(ana)
        departamento.asignar_gerente(luis)
        departamento.quitar_empleado(ana)
        self.assertEqual(departamento.empleados, [luis])
        self.assertIsNone(ana.departamento)

    def test_no_se_pertenece_a_dos_departamentos(self):
        ana, luis = empleado(), empleado(2)
        Departamento(None, "Tecnología", ana)
        otro = Departamento(None, "Finanzas", luis)
        with self.assertRaises(ValueError):
            otro.agregar_empleado(ana)

    def test_modificar_listas_copiadas_no_altera_las_relaciones(self):
        ana = empleado()
        departamento = Departamento(None, "Tecnología", ana)
        departamento.empleados.clear()
        proyecto = Proyecto(None, "Agua", "Sensores", date(2026, 3, 1), [ana])
        proyecto.empleados_asignados.clear()
        self.assertEqual(departamento.empleados, [ana])
        self.assertEqual(proyecto.empleados_asignados, [ana])

    def test_un_empleado_participa_en_varios_proyectos(self):
        ana, luis = empleado(), empleado(2)
        uno = Proyecto(None, "Agua", "Sensores", date.today(), [ana, luis])
        dos = Proyecto(None, "Luz", "Medidores", date.today(), [ana])
        uno.asignar_empleado(ana)
        self.assertEqual(len(uno.empleados_asignados), 2)
        self.assertIn(ana, dos.empleados_asignados)

    def test_registrar_horas_exige_asignacion_y_conserva_fecha(self):
        ana = empleado(id_empleado=1)
        proyecto = Proyecto(2, "Agua", "Sensores", date.today())
        with self.assertRaises(ValueError):
            ana.registrar_horas(date(2026, 1, 10), proyecto, 2, "Revisión")
        proyecto.asignar_empleado(ana)
        registro = ana.registrar_horas(date(2026, 1, 10), proyecto, 2.5, "Revisión")
        self.assertEqual(registro.fecha, date(2026, 1, 10))
        self.assertEqual((registro.id_empleado, registro.id_proyecto), (1, 2))
        self.assertIs(ana.registros_tiempo[0], proyecto.registros_tiempo[0])

    def test_horas_invalidas_no_agregan_registros(self):
        ana = empleado()
        proyecto = Proyecto(None, "Agua", "Sensores", date.today(), [ana])
        for valor in (0, -1, 24.01, 1.001, True, "nan"):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                ana.registrar_horas(date.today(), proyecto, valor, "Revisión")
        self.assertEqual(ana.registros_tiempo, [])
        self.assertEqual(proyecto.registros_tiempo, [])

    def test_informe_rechaza_datos_incompletos_o_repetidos(self):
        informe = Informe(None, "Resumen")
        with self.assertRaises(ValueError):
            informe.generar([empleado()], [], [], [])
        persona = empleado(id_empleado=1)
        with self.assertRaises(ValueError):
            informe.generar([persona, persona], [], [], [])
        registro = RegistroDeTiempo(1, date.today(), 2, "Tareas", 1, 9)
        with self.assertRaises(ValueError):
            informe.generar([persona], [], [], [registro])
