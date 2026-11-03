import sqlite3
from contextlib import closing
from src.dependencia import Administrador, Usuario
from src.persistencia import DAOError, EmpleadoDAO, UsuarioDAO
from tests.apoyo import BaseBD, CLAVE, HASH_PRUEBA, empleado


class CuentasYEmpleadosTest(BaseBD):
    def test_cuenta_se_guarda_autentica_actualiza_y_desactiva(self):
        cuenta = self.cuenta()
        self.assertEqual(UsuarioDAO.autenticar("ANA_PRUEBA", CLAVE).id_usuario, cuenta.id_usuario)
        self.assertIsNone(UsuarioDAO.autenticar("ana_prueba", "equivocada"))
        cuenta.nombre_usuario = "otro_nombre"
        cuenta.establecer_contrasena("Nueva2026*")
        self.assertTrue(UsuarioDAO.actualizar(cuenta))
        self.assertIsNone(UsuarioDAO.autenticar("ana_prueba", CLAVE))
        self.assertIsNotNone(UsuarioDAO.autenticar("otro_nombre", "Nueva2026*"))
        cuenta.desactivar()
        UsuarioDAO.actualizar(cuenta)
        self.assertIsNone(UsuarioDAO.autenticar("otro_nombre", "Nueva2026*"))

    def test_tipo_admin_se_recupera_y_no_se_cambia_por_actualizar(self):
        admin = self.cuenta(admin=True)
        self.assertIsInstance(UsuarioDAO.buscar_por_id(admin.id_usuario), Administrador)
        falsa = Usuario(admin.id_usuario, admin.nombre_usuario, HASH_PRUEBA)
        with self.assertRaises(DAOError):
            UsuarioDAO.actualizar(falsa)

    def test_duplicado_no_deja_cuenta_ni_admin_a_medias(self):
        self.cuenta()
        with self.assertRaises(DAOError):
            self.cuenta(admin=True)
        self.assertEqual(len(UsuarioDAO.listar()), 1)
        self.assertFalse(UsuarioDAO.hay_administradores())

    def test_ultimo_administrador_activo_no_se_desactiva(self):
        admin = self.cuenta(admin=True)
        admin.desactivar()
        with self.assertRaises(DAOError):
            UsuarioDAO.actualizar(admin)
        self.assertTrue(UsuarioDAO.buscar_por_id(admin.id_usuario).activo)

    def test_con_otro_admin_activo_se_puede_desactivar(self):
        admin = self.cuenta(admin=True)
        self.cuenta("segundo_admin", admin=True)
        admin.desactivar()
        self.assertTrue(UsuarioDAO.actualizar(admin))
        self.assertFalse(UsuarioDAO.buscar_por_id(admin.id_usuario).activo)

    def test_empleado_tiene_id_independiente_y_cuenta_opcional(self):
        self.cuenta("primero")
        cuenta = self.cuenta("segundo")
        persona = self.persona()
        self.assertNotEqual(cuenta.id_usuario, persona.id_empleado)
        self.assertIsNone(EmpleadoDAO.buscar_por_id(persona.id_empleado).usuario)
        self.assertEqual(len(UsuarioDAO.listar()), 2)

    def test_crud_empleado_recupera_todos_los_datos(self):
        persona = self.persona(nombre="José Muñoz")
        guardado = EmpleadoDAO.buscar_por_id(persona.id_empleado)
        for campo in (
            "identificacion",
            "nombre",
            "correo",
            "direccion",
            "telefono",
            "salario",
            "fecha_inicio_contrato",
        ):
            self.assertEqual(getattr(guardado, campo), getattr(persona, campo))
        persona.nombre = "José Muñoz Díaz"
        persona.salario = 950000
        self.assertTrue(EmpleadoDAO.actualizar(persona))
        self.assertEqual(EmpleadoDAO.buscar_por_id(persona.id_empleado).salario, 950000)
        self.assertTrue(EmpleadoDAO.eliminar(persona.id_empleado))
        self.assertIsNone(EmpleadoDAO.buscar_por_id(persona.id_empleado))

    def test_no_hay_datos_personales_en_claro_en_la_fila(self):
        persona = self.persona(nombre="NombreConfidencial", direccion="DireccionReservada987")
        with closing(sqlite3.connect(self.base)) as conexion, conexion:
            fila = conexion.execute("SELECT * FROM empleado").fetchone()
        for dato in (
            persona.nombre,
            persona.direccion,
            persona.correo,
            persona.identificacion,
            persona.telefono,
        ):
            self.assertNotIn(dato, str(fila))
        self.assertEqual(
            EmpleadoDAO.buscar_por_correo(persona.correo.upper()).id_empleado, persona.id_empleado
        )
        self.assertEqual(
            EmpleadoDAO.buscar_por_identificacion("emp-0001").id_empleado, persona.id_empleado
        )

    def test_identificacion_y_correo_unicos_aunque_estan_cifrados(self):
        persona = self.persona()
        for cambios in ({"identificacion": "EMP-0001"}, {"correo": persona.correo.upper()}):
            with self.subTest(cambios=cambios), self.assertRaises(DAOError):
                EmpleadoDAO.insertar(empleado(2, **cambios))
        self.assertEqual(len(EmpleadoDAO.listar()), 1)

    def test_actualizacion_rechazada_no_modifica_otros_datos(self):
        uno, dos = self.persona(), self.persona(2)
        dos.nombre = "Cambio que debe revertirse"
        dos.correo = uno.correo
        with self.assertRaises(DAOError):
            EmpleadoDAO.actualizar(dos)
        self.assertEqual(EmpleadoDAO.buscar_por_id(dos.id_empleado).nombre, "Persona 2")

    def test_cuenta_y_empleado_se_vinculan_y_desvinculan(self):
        cuenta, persona = self.cuenta(), self.persona()
        EmpleadoDAO.vincular_cuenta(persona.id_empleado, cuenta.id_usuario)
        self.assertEqual(
            EmpleadoDAO.buscar_por_usuario(cuenta.id_usuario).id_empleado, persona.id_empleado
        )
        EmpleadoDAO.desvincular_cuenta(persona.id_empleado)
        self.assertIsNone(EmpleadoDAO.buscar_por_usuario(cuenta.id_usuario))
        self.assertIsNotNone(UsuarioDAO.buscar_por_id(cuenta.id_usuario))

    def test_cuenta_solo_puede_tener_un_empleado(self):
        cuenta, uno, dos = self.cuenta(), self.persona(), self.persona(2)
        EmpleadoDAO.vincular_cuenta(uno.id_empleado, cuenta.id_usuario)
        with self.assertRaises(DAOError):
            EmpleadoDAO.vincular_cuenta(dos.id_empleado, cuenta.id_usuario)
        self.assertIsNone(EmpleadoDAO.buscar_por_id(dos.id_empleado).usuario)

    def test_empleado_no_puede_tener_dos_cuentas(self):
        uno, dos, persona = self.cuenta(), self.cuenta("segundo"), self.persona()
        EmpleadoDAO.vincular_cuenta(persona.id_empleado, uno.id_usuario)
        with self.assertRaises(DAOError):
            EmpleadoDAO.vincular_cuenta(persona.id_empleado, dos.id_usuario)
        self.assertEqual(
            EmpleadoDAO.buscar_por_id(persona.id_empleado).usuario.id_usuario, uno.id_usuario
        )

    def test_desactivar_conserva_empleado_y_borrar_empleado_conserva_cuenta(self):
        cuenta, persona = self.cuenta(), self.persona()
        EmpleadoDAO.vincular_cuenta(persona.id_empleado, cuenta.id_usuario)
        cuenta.desactivar()
        UsuarioDAO.actualizar(cuenta)
        self.assertFalse(EmpleadoDAO.buscar_por_id(persona.id_empleado).usuario.activo)
        EmpleadoDAO.eliminar(persona.id_empleado)
        self.assertIsNotNone(UsuarioDAO.buscar_por_id(cuenta.id_usuario))

    def test_cuenta_inexistente_inactiva_o_sin_guardar_no_se_vincula(self):
        persona = self.persona()
        cuenta = self.cuenta()
        cuenta.desactivar()
        UsuarioDAO.actualizar(cuenta)
        for identificador in (999, cuenta.id_usuario):
            with self.assertRaises(DAOError):
                EmpleadoDAO.vincular_cuenta(persona.id_empleado, identificador)
        with self.assertRaises(DAOError):
            EmpleadoDAO.insertar(empleado(2, usuario=Usuario(None, "sin_guardar", HASH_PRUEBA)))

    def test_texto_con_apostrofe_se_trata_como_dato(self):
        persona = self.persona(nombre="O'Connor; DROP TABLE empleado; --")
        self.assertEqual(EmpleadoDAO.buscar_por_id(persona.id_empleado).nombre, persona.nombre)
        self.assertIsNone(EmpleadoDAO.buscar_por_id("1 OR 1=1"))
        self.assertEqual(len(EmpleadoDAO.listar()), 1)

    def test_objeto_guardado_no_se_inserta_dos_veces(self):
        persona = self.persona()
        with self.assertRaises(DAOError):
            EmpleadoDAO.insertar(persona)
        self.assertEqual(len(EmpleadoDAO.listar()), 1)

    def test_actualizar_ficha_no_sobrescribe_cuenta_cambiada_despues(self):
        persona, cuenta = self.persona(), self.cuenta()
        EmpleadoDAO.vincular_cuenta(persona.id_empleado, cuenta.id_usuario)
        persona.nombre = "Nombre corregido"
        EmpleadoDAO.actualizar(persona)
        self.assertEqual(
            EmpleadoDAO.buscar_por_id(persona.id_empleado).usuario.id_usuario, cuenta.id_usuario
        )
