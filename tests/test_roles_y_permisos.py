"""Casos del laboratorio de la clase 5, con bases temporales."""

import io
import sqlite3
from contextlib import closing
from datetime import date
from unittest.mock import patch

from src import main
from src.dependencia import Usuario, Administrador, RegistroDeTiempo
from src.persistencia import (
    EmpleadoDAO,
    UsuarioDAO,
    ProyectoDAO,
    RegistroTiempoDAO,
    DAOError,
    crear_tablas,
)
from src.servicios.autenticacion import autenticar, cerrar_sesion
from src.servicios.permisos import exigir_sesion, exigir_admin
from src.servicios import gestion_empleados, gestion_usuarios, mi_cuenta
from src.persistencia.semilla_bd import cargar_semilla
from tests.apoyo import BaseBD, CLAVE


class RolesTest(BaseBD):
    def preparar_cuentas(self):
        admin = self.cuenta("admin_prueba", admin=True)
        ana = self.cuenta("ana_prueba")
        luis = self.cuenta("luis_prueba")
        return self.sesion(admin, 90), self.sesion(ana, 1), self.sesion(luis, 2)

    def test_rol_solo_admite_admin_y_empleado(self):
        self.assertEqual(Usuario(None, "normal").rol, "empleado")
        self.assertEqual(Administrador(None, "admin").rol, "admin")
        for rol in (None, "jefe", "ADMIN", 1, ""):
            with self.subTest(rol=rol), self.assertRaises(ValueError):
                Usuario(None, "prueba", rol=rol)

    def test_dao_guarda_rol_y_recupera_tipo(self):
        admin = self.cuenta("admin", admin=True)
        normal = self.cuenta("empleado")
        self.assertEqual(UsuarioDAO.buscar_por_id(admin.id_usuario).rol, "admin")
        self.assertIsInstance(UsuarioDAO.buscar_por_nombre("admin"), Administrador)
        self.assertEqual(UsuarioDAO.buscar_por_id(normal.id_usuario).rol, "empleado")
        with self.assertRaises(ValueError):
            UsuarioDAO.insertar(Usuario(None, "falso_admin", rol="admin"))

    def test_base_rechaza_rol_invalido(self):
        cuenta = self.cuenta()
        with closing(sqlite3.connect(self.base)) as conexion, conexion:
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute(
                    "UPDATE usuario SET rol = 'jefe' WHERE id_usuario = ?", (cuenta.id_usuario,)
                )

    def test_login_arma_sesion_y_rechaza_cuenta_sin_empleado(self):
        cuenta = self.cuenta()
        with self.assertRaises(PermissionError):
            autenticar(cuenta.nombre_usuario, CLAVE)
        sesion = self.sesion(cuenta)
        self.assertEqual(set(sesion), {"id", "empleado_id", "nombre_usuario", "rol"})
        self.assertEqual(sesion["id"], cuenta.id_usuario)
        self.assertIsNone(autenticar(cuenta.nombre_usuario, "incorrecta"))

    def test_admin_lista_y_empleado_se_rechaza_antes_de_listar(self):
        admin, ana, _ = self.preparar_cuentas()
        self.assertEqual(len(gestion_empleados.listar_todos(admin)), 3)
        with patch("src.servicios.gestion_empleados.EmpleadoDAO.listar") as listar:
            with self.assertRaises(PermissionError):
                gestion_empleados.listar_todos(ana)
        listar.assert_not_called()

    def test_empleado_no_puede_crear_actualizar_ni_eliminar_otra_ficha(self):
        _, ana, luis = self.preparar_cuentas()
        ajeno = EmpleadoDAO.buscar_por_id(luis["empleado_id"])
        for operacion in (
            lambda: gestion_empleados.insertar(ana, ajeno),
            lambda: gestion_empleados.actualizar(ana, ajeno),
            lambda: gestion_empleados.eliminar(ana, ajeno.id_empleado),
            lambda: gestion_empleados.vincular_cuenta(ana, ajeno.id_empleado, ana["id"]),
        ):
            with self.assertRaises(PermissionError):
                operacion()
        self.assertIsNotNone(EmpleadoDAO.buscar_por_id(ajeno.id_empleado))

    def test_las_otras_areas_administrativas_tambien_exigen_admin(self):
        from src.servicios import (
            gestion_departamentos,
            gestion_proyectos,
            gestion_registros,
            gestion_informes,
        )

        _, ana, _ = self.preparar_cuentas()
        for servicio in (
            gestion_departamentos,
            gestion_proyectos,
            gestion_registros,
            gestion_informes,
            gestion_usuarios,
        ):
            with self.subTest(servicio=servicio.__name__), self.assertRaises(PermissionError):
                servicio.listar(ana)

    def test_mi_ficha_y_mis_registros_no_mezclan_empleados(self):
        _, ana, luis = self.preparar_cuentas()
        proyecto = self.proyecto()
        for sesion, horas in ((ana, 2), (luis, 3)):
            ProyectoDAO.asignar_empleado(proyecto.id_proyecto, sesion["empleado_id"])
            RegistroTiempoDAO.insertar(
                RegistroDeTiempo(
                    None,
                    date(2026, 3, 1),
                    horas,
                    "Trabajo",
                    sesion["empleado_id"],
                    proyecto.id_proyecto,
                )
            )
        self.assertEqual(mi_cuenta.mi_ficha(ana).id_empleado, ana["empleado_id"])
        registros = mi_cuenta.mis_registros(ana)
        self.assertEqual(len(registros), 1)
        self.assertEqual(registros[0].id_empleado, ana["empleado_id"])
        self.assertEqual(registros[0].horas, 2)

    def test_actualizar_nombre_correo_conserva_salario_rol_relaciones_y_al_otro_empleado(self):
        _, ana, luis = self.preparar_cuentas()
        anterior = mi_cuenta.mi_ficha(ana)
        ajeno = mi_cuenta.mi_ficha(luis)
        self.assertTrue(
            mi_cuenta.actualizar_mis_datos(ana, "Ana Modificada", "ana.nueva@ejemplo.cl")
        )
        nueva = mi_cuenta.mi_ficha(ana)
        self.assertEqual((nueva.nombre, nueva.correo), ("Ana Modificada", "ana.nueva@ejemplo.cl"))
        for campo in (
            "id_empleado",
            "identificacion",
            "salario",
            "direccion",
            "telefono",
            "fecha_inicio_contrato",
            "id_departamento",
        ):
            self.assertEqual(getattr(nueva, campo), getattr(anterior, campo))
        self.assertEqual(nueva.usuario.id_usuario, anterior.usuario.id_usuario)
        self.assertEqual(nueva.usuario.rol, "empleado")
        self.assertEqual(mi_cuenta.mi_ficha(luis).nombre, ajeno.nombre)
        self.assertEqual(mi_cuenta.mi_ficha(luis).correo, ajeno.correo)

    def test_edicion_propia_rechaza_datos_invalidos_y_correo_ajeno(self):
        _, ana, luis = self.preparar_cuentas()
        for nombre, correo in (("A", "ana@ejemplo.cl"), ("Ana", "no es correo")):
            with self.assertRaises(ValueError):
                mi_cuenta.actualizar_mis_datos(ana, nombre, correo)
        with self.assertRaises(DAOError):
            mi_cuenta.actualizar_mis_datos(ana, "Ana", mi_cuenta.mi_ficha(luis).correo)
        self.assertEqual(mi_cuenta.mi_ficha(ana).nombre, "Persona 1")

    def test_cuenta_habitual_siempre_es_empleado_y_queda_vinculada(self):
        admin, ana, _ = self.preparar_cuentas()
        ficha = self.persona(3)
        with self.assertRaises(PermissionError):
            gestion_usuarios.registrar_cuenta(ana, ficha.id_empleado, "otra", CLAVE)
        cuenta = gestion_usuarios.registrar_cuenta(admin, ficha.id_empleado, "otra", CLAVE)
        self.assertEqual(cuenta.rol, "empleado")
        self.assertEqual(autenticar("otra", CLAVE)["empleado_id"], ficha.id_empleado)
        with self.assertRaises(DAOError):
            gestion_usuarios.registrar_cuenta(admin, ficha.id_empleado, "duplicada", CLAVE)
        self.assertIsNone(UsuarioDAO.buscar_por_nombre("duplicada"))

    def test_no_se_puede_elevar_el_rol_al_actualizar_la_cuenta(self):
        admin, ana, _ = self.preparar_cuentas()
        cuenta = UsuarioDAO.buscar_por_id(ana["id"])
        cuenta.rol = "admin"
        with self.assertRaises(DAOError):
            gestion_usuarios.actualizar(admin, cuenta)
        self.assertEqual(UsuarioDAO.buscar_por_id(ana["id"]).rol, "empleado")

    def test_cerrar_sesion_impide_seguir_usandola(self):
        admin, ana, _ = self.preparar_cuentas()
        cerrar_sesion(ana)
        with self.assertRaises(PermissionError):
            mi_cuenta.mi_ficha(ana)
        cerrar_sesion(admin)
        with self.assertRaises(PermissionError):
            gestion_empleados.listar_todos(admin)

    def test_sesion_alterada_desactivada_o_desvinculada_se_rechaza(self):
        _, ana, luis = self.preparar_cuentas()
        for falsa in (
            None,
            {},
            {**ana, "empleado_id": True},
            {**ana, "rol": "admin"},
            {**ana, "empleado_id": luis["empleado_id"]},
        ):
            with self.assertRaises(PermissionError):
                exigir_sesion(falsa)
        cuenta = UsuarioDAO.buscar_por_id(ana["id"])
        cuenta.desactivar()
        UsuarioDAO.actualizar(cuenta)
        with self.assertRaises(PermissionError):
            exigir_sesion(ana)
        EmpleadoDAO.desvincular_cuenta(luis["empleado_id"])
        with self.assertRaises(PermissionError):
            exigir_sesion(luis)

    def test_migracion_agrega_rol_sin_cambiar_cuentas_contrasenas_ni_empleados(self):
        admin, ana, _ = self.preparar_cuentas()
        hash_antes = UsuarioDAO.buscar_por_id(admin["id"]).contrasena_hash
        with closing(sqlite3.connect(self.base)) as conexion, conexion:
            conexion.execute("ALTER TABLE usuario DROP COLUMN rol")
        crear_tablas()
        crear_tablas()
        self.assertEqual(UsuarioDAO.buscar_por_id(admin["id"]).rol, "admin")
        self.assertEqual(UsuarioDAO.buscar_por_id(ana["id"]).rol, "empleado")
        self.assertEqual(UsuarioDAO.buscar_por_id(admin["id"]).contrasena_hash, hash_antes)
        self.assertEqual(len(EmpleadoDAO.listar()), 3)
        self.assertIsNotNone(autenticar("ana_prueba", CLAVE))

    def test_semilla_repetida_no_eleva_cuenta_normal_a_admin(self):
        cuenta = self.cuenta("admin_demo")
        with self.assertRaises(ValueError), patch("sys.stdout", io.StringIO()):
            cargar_semilla()
        self.assertEqual(UsuarioDAO.buscar_por_id(cuenta.id_usuario).rol, "empleado")

    def test_menu_cierra_sesion_y_pide_otro_login(self):
        with patch("sys.stdout", io.StringIO()):
            cargar_semilla()
        salida = io.StringIO()
        with patch("sys.argv", ["ecotech"]), patch("sys.stdout", salida), patch(
            "builtins.input", side_effect=["ana_demo", "9", "luis_demo", "0"]
        ), patch("getpass.getpass", return_value="Demo2026*"):
            self.assertEqual(main.main(), 0)
        self.assertIn("Bienvenido, ana_demo", salida.getvalue())
        self.assertIn("Bienvenido, luis_demo", salida.getvalue())
        self.assertNotIn("Administrar empleados", salida.getvalue())
