from datetime import date
from src.dependencia import Departamento, Proyecto, RegistroDeTiempo
from src.persistencia import (
    DAOError, DepartamentoDAO, EmpleadoDAO, ProyectoDAO, RegistroTiempoDAO, UsuarioDAO,
)
from tests.apoyo import BaseBD, empleado


class RelacionesYHorasTest(BaseBD):
    def setUp(self):
        super().setUp()
        self.ana, self.luis = self.persona(), self.persona(2)
        self.departamento = DepartamentoDAO.insertar(
            Departamento(None, "Tecnología", self.ana, [self.ana, self.luis]))
        self.proyecto = self.proyecto("Agua")
        ProyectoDAO.asignar_empleado(self.proyecto.id_proyecto, self.ana.id_empleado)

    def registro(self, horas=4, persona=None, proyecto=None, fecha=date(2026, 3, 10)):
        persona = persona or self.ana
        proyecto = proyecto or self.proyecto
        return RegistroTiempoDAO.insertar(RegistroDeTiempo(
            None, fecha, horas, "Revisar sensores", persona.id_empleado, proyecto.id_proyecto))

    def test_recupera_gerente_miembros_y_horas_desde_la_base(self):
        registro = self.registro()
        departamento = DepartamentoDAO.buscar_por_id(self.departamento.id_departamento)
        ana = EmpleadoDAO.buscar_por_id(self.ana.id_empleado)
        proyecto = ProyectoDAO.buscar_por_id(self.proyecto.id_proyecto)
        self.assertEqual(departamento.gerente, ana)
        self.assertEqual(len(departamento.empleados), 2)
        self.assertEqual(ana.id_departamento, departamento.id_departamento)
        self.assertEqual(ana.registros_tiempo[0].id_registro, registro.id_registro)
        self.assertEqual(proyecto.registros_tiempo[0].id_registro, registro.id_registro)

    def test_no_se_quita_ni_elimina_al_gerente_actual(self):
        with self.assertRaises(DAOError):
            DepartamentoDAO.quitar_empleado(self.departamento.id_departamento, self.ana.id_empleado)
        with self.assertRaises(DAOError):
            EmpleadoDAO.eliminar(self.ana.id_empleado)
        self.assertEqual(len(DepartamentoDAO.buscar_por_id(self.departamento.id_departamento).empleados), 2)

    def test_reemplazar_gerente_permite_quitar_al_anterior(self):
        self.departamento.asignar_gerente(self.luis)
        DepartamentoDAO.actualizar(self.departamento)
        DepartamentoDAO.quitar_empleado(self.departamento.id_departamento, self.ana.id_empleado)
        actual = DepartamentoDAO.buscar_por_id(self.departamento.id_departamento)
        self.assertEqual(actual.gerente.id_empleado, self.luis.id_empleado)
        self.assertEqual(len(actual.empleados), 1)
        self.assertIsNone(EmpleadoDAO.buscar_por_id(self.ana.id_empleado).departamento)

    def test_eliminar_departamento_conserva_empleados_y_horas(self):
        registro = self.registro()
        DepartamentoDAO.eliminar(self.departamento.id_departamento)
        self.assertEqual(len(EmpleadoDAO.listar()), 2)
        self.assertIsNone(EmpleadoDAO.buscar_por_id(self.ana.id_empleado).departamento)
        self.assertIsNotNone(RegistroTiempoDAO.buscar_por_id(registro.id_registro))

    def test_reasignacion_cambia_un_solo_departamento_y_no_al_gerente(self):
        tercera = self.persona(3)
        otro = DepartamentoDAO.insertar(Departamento(None, "Ventas", tercera))
        with self.assertRaises(DAOError):
            DepartamentoDAO.agregar_empleado(otro.id_departamento, self.luis.id_empleado)
        DepartamentoDAO.reasignar_empleado(self.luis.id_empleado, otro.id_departamento)
        self.assertEqual(EmpleadoDAO.buscar_por_id(self.luis.id_empleado).id_departamento, otro.id_departamento)
        with self.assertRaises(DAOError):
            DepartamentoDAO.reasignar_empleado(self.ana.id_empleado, otro.id_departamento)
        self.assertEqual(EmpleadoDAO.buscar_por_id(self.ana.id_empleado).id_departamento, self.departamento.id_departamento)

    def test_destino_inexistente_no_pierde_la_asignacion_anterior(self):
        with self.assertRaises(DAOError):
            DepartamentoDAO.reasignar_empleado(self.luis.id_empleado, 999)
        self.assertEqual(EmpleadoDAO.buscar_por_id(self.luis.id_empleado).id_departamento, self.departamento.id_departamento)

    def test_departamento_con_gerente_sin_guardar_no_se_inserta(self):
        nuevo = Departamento(None, "Nuevo", empleado(3))
        with self.assertRaises(DAOError):
            DepartamentoDAO.insertar(nuevo)
        self.assertIsNone(nuevo.id_departamento)
        self.assertEqual(len(DepartamentoDAO.listar()), 1)

    def test_actualizar_ficha_no_cambia_el_departamento(self):
        atrasada = EmpleadoDAO.buscar_por_id(self.luis.id_empleado)
        DepartamentoDAO.quitar_empleado(self.departamento.id_departamento, self.luis.id_empleado)
        atrasada.nombre = "Luis actualizado"
        EmpleadoDAO.actualizar(atrasada)
        self.assertIsNone(EmpleadoDAO.buscar_por_id(self.luis.id_empleado).id_departamento)

    def test_muchos_empleados_y_muchos_proyectos_sin_duplicados(self):
        otro = BaseBD.proyecto(self, "Luz")
        ProyectoDAO.asignar_empleado(self.proyecto.id_proyecto, self.luis.id_empleado)
        ProyectoDAO.asignar_empleado(otro.id_proyecto, self.ana.id_empleado)
        self.assertFalse(ProyectoDAO.asignar_empleado(otro.id_proyecto, self.ana.id_empleado))
        self.assertEqual(len(ProyectoDAO.buscar_por_id(self.proyecto.id_proyecto).empleados_asignados), 2)
        self.assertIn(self.ana, ProyectoDAO.buscar_por_id(otro.id_proyecto).empleados_asignados)

    def test_proyecto_revierte_alta_si_falla_una_asignacion_inicial(self):
        proyecto = Proyecto(None, "Fallido", "Ejemplo", date.today(), [empleado(3)])
        with self.assertRaises(DAOError):
            ProyectoDAO.insertar(proyecto)
        self.assertIsNone(proyecto.id_proyecto)
        self.assertIsNone(ProyectoDAO.buscar_por_nombre("Fallido"))

    def test_actualizar_y_eliminar_proyecto_sin_horas(self):
        self.proyecto.nombre = "Agua actualizada"
        self.proyecto.descripcion = "Sensores nuevos"
        ProyectoDAO.actualizar(self.proyecto)
        self.assertEqual(ProyectoDAO.buscar_por_id(self.proyecto.id_proyecto).descripcion, "Sensores nuevos")
        self.assertTrue(ProyectoDAO.eliminar(self.proyecto.id_proyecto))

    def test_horas_exigen_empleado_proyecto_y_asignacion(self):
        with self.assertRaises(DAOError):
            self.registro(persona=self.luis)
        for id_empleado, id_proyecto in ((999, self.proyecto.id_proyecto), (self.ana.id_empleado, 999), (None, None)):
            with self.subTest(ids=(id_empleado, id_proyecto)), self.assertRaises(DAOError):
                RegistroTiempoDAO.insertar(RegistroDeTiempo(None, date.today(), 1, "Tareas", id_empleado, id_proyecto))
        self.assertEqual(RegistroTiempoDAO.listar(), [])

    def test_limite_diario_suma_todos_los_proyectos(self):
        otro = BaseBD.proyecto(self, "Luz")
        ProyectoDAO.asignar_empleado(otro.id_proyecto, self.ana.id_empleado)
        self.registro(20)
        self.registro(4, proyecto=otro)
        with self.assertRaises(DAOError):
            self.registro(0.01, proyecto=otro)
        self.assertEqual(sum(r.horas for r in RegistroTiempoDAO.listar()), 24)

    def test_otro_dia_permite_horas_y_actualizar_no_duplica_el_propio_total(self):
        registro = self.registro(24)
        registro.descripcion_tareas = "Descripción corregida"
        self.assertTrue(RegistroTiempoDAO.actualizar(registro))
        self.registro(24, fecha=date(2026, 3, 11))
        self.assertEqual(RegistroTiempoDAO.total_horas_proyecto(self.proyecto.id_proyecto), 48)

    def test_actualizacion_excesiva_no_modifica_la_base(self):
        primero = self.registro(20)
        segundo = self.registro(4)
        primero.horas = 21
        with self.assertRaises(DAOError):
            RegistroTiempoDAO.actualizar(primero)
        self.assertEqual(RegistroTiempoDAO.buscar_por_id(primero.id_registro).horas, 20)
        self.assertEqual(RegistroTiempoDAO.buscar_por_id(segundo.id_registro).horas, 4)

    def test_no_se_cambia_el_empleado_o_proyecto_de_un_registro(self):
        registro = self.registro()
        registro.id_empleado = self.luis.id_empleado
        with self.assertRaises(DAOError):
            RegistroTiempoDAO.actualizar(registro)
        self.assertEqual(RegistroTiempoDAO.buscar_por_id(registro.id_registro).id_empleado, self.ana.id_empleado)

    def test_desasignar_conserva_historial_y_permite_corregirlo(self):
        registro = self.registro()
        ProyectoDAO.desasignar_empleado(self.proyecto.id_proyecto, self.ana.id_empleado)
        registro.horas = 5
        self.assertTrue(RegistroTiempoDAO.actualizar(registro))
        self.assertEqual(RegistroTiempoDAO.buscar_por_id(registro.id_registro).horas, 5)
        with self.assertRaises(DAOError):
            self.registro()

    def test_empleado_y_proyecto_con_horas_no_se_borran(self):
        self.registro()
        DepartamentoDAO.eliminar(self.departamento.id_departamento)
        with self.assertRaises(DAOError):
            EmpleadoDAO.eliminar(self.ana.id_empleado)
        with self.assertRaises(DAOError):
            ProyectoDAO.eliminar(self.proyecto.id_proyecto)

    def test_borrar_horas_es_explicito_y_desactivar_cuenta_no_las_borra(self):
        registro = self.registro()
        cuenta = self.cuenta()
        EmpleadoDAO.vincular_cuenta(self.ana.id_empleado, cuenta.id_usuario)
        cuenta.desactivar()
        UsuarioDAO.actualizar(cuenta)
        self.assertIsNotNone(RegistroTiempoDAO.buscar_por_id(registro.id_registro))
        RegistroTiempoDAO.eliminar(registro.id_registro)
        self.assertIsNone(RegistroTiempoDAO.buscar_por_id(registro.id_registro))
        self.assertTrue(ProyectoDAO.eliminar(self.proyecto.id_proyecto))
