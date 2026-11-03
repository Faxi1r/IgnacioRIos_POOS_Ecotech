import io
import sqlite3
from unittest.mock import Mock, patch

from src import main
from src.dependencia import Administrador
from src.menus import comunes, menu_informe, menu_personal, menu_usuario
from src.persistencia import EmpleadoDAO, InformeDAO, UsuarioDAO, crear_tablas, DAOError
from src.persistencia.semilla_bd import cargar_semilla
from tests.apoyo import BaseBD, CLAVE


class AccesoTest(BaseBD):
    def test_login_correcto_recupera_tipo_real_y_errado_tiene_tres_intentos(self):
        self.sesion(self.cuenta("admin_prueba", admin=True))
        with patch("builtins.input", return_value="admin_prueba"), patch(
            "getpass.getpass", return_value=CLAVE
        ):
            self.assertEqual(main.iniciar_sesion()["rol"], "admin")
        with patch("builtins.input", return_value="admin_prueba") as entrada, patch(
            "getpass.getpass", return_value="incorrecta"
        ), patch("sys.stdout", io.StringIO()):
            self.assertIsNone(main.iniciar_sesion())
            self.assertEqual(entrada.call_count, 3)

    def test_usuario_comun_abre_su_menu_y_no_el_de_administracion(self):
        cuenta = self.cuenta()
        sesion = self.sesion(cuenta)
        with patch("builtins.input", side_effect=["11", "0"]), patch(
            "sys.stdout", io.StringIO()
        ), patch("src.main.menu_personal") as personal, patch("src.main.menu_usuario") as usuarios:
            main.menu_principal(sesion)
        personal.assert_called_once_with(sesion)
        usuarios.assert_not_called()

    def test_administrador_abre_menu_con_su_identidad(self):
        cuenta = self.cuenta(admin=True)
        sesion = self.sesion(cuenta)
        with patch("builtins.input", side_effect=["8", "0"]), patch(
            "sys.stdout", io.StringIO()
        ), patch("src.main.menu_usuario") as usuarios:
            main.menu_principal(sesion)
        usuarios.assert_called_once_with(sesion)

    def test_no_se_puede_desactivar_la_propia_sesion_desde_el_menu(self):
        cuenta = self.cuenta(admin=True)
        sesion = self.sesion(cuenta)
        with patch("src.menus.menu_usuario.seleccionar_usuario", return_value=cuenta), patch(
            "builtins.input"
        ) as entrada, patch("sys.stdout", io.StringIO()):
            menu_usuario.desactivar_usuario(sesion)
        entrada.assert_not_called()
        self.assertTrue(UsuarioDAO.buscar_por_id(cuenta.id_usuario).activo)

    def test_submenu_deniega_a_usuarios_sin_permiso(self):
        cuenta, accion = self.cuenta(), Mock()
        sesion = self.sesion(cuenta)
        with patch("builtins.input") as entrada, patch("sys.stdout", io.StringIO()):
            comunes.submenu("Administración", {"1": ("Modificar", accion)}, sesion, "empleados")
        entrada.assert_not_called()
        accion.assert_not_called()

    def test_submenu_revoca_acceso_si_desactivan_la_cuenta_durante_sesion(self):
        cuenta, accion = self.cuenta(), Mock()
        sesion = self.sesion(cuenta)

        def desactivar_al_elegir(mensaje):
            cuenta.desactivar()
            UsuarioDAO.actualizar(cuenta)
            return "1"

        with patch("builtins.input", side_effect=desactivar_al_elegir), patch(
            "sys.stdout", io.StringIO()
        ):
            comunes.submenu("Personal", {"1": ("Ver", accion)}, sesion, "mi_cuenta")
        accion.assert_not_called()

    def test_cuenta_comun_solo_ve_a_su_empleado(self):
        cuenta = self.cuenta()
        ana = self.persona(nombre="Ana Propia")
        self.persona(2, nombre="Luis Ajeno")
        EmpleadoDAO.vincular_cuenta(ana.id_empleado, cuenta.id_usuario)
        salida = io.StringIO()
        with patch("sys.stdout", salida):
            menu_personal.ver_mis_datos(main.autenticar(cuenta.nombre_usuario, CLAVE))
        self.assertIn("Ana Propia", salida.getvalue())
        self.assertNotIn("Luis Ajeno", salida.getvalue())

    def test_cuenta_sin_empleado_no_pide_identidad_ajena(self):
        cuenta = self.cuenta()
        with patch("builtins.input") as entrada, patch("sys.stdout", io.StringIO()):
            with self.assertRaises(PermissionError):
                main.autenticar(cuenta.nombre_usuario, CLAVE)
        entrada.assert_not_called()

    def test_primer_admin_no_se_crea_de_nuevo(self):
        with patch("sys.argv", ["ecotech", "--crear-admin"]), patch(
            "builtins.input",
            side_effect=[
                "primer_admin",
                "ADMIN0001",
                "Admin Inicial",
                "admin@ejemplo.cl",
                "900000",
                "Calle 1",
                "912345678",
                "2026-03-01",
            ],
        ), patch("getpass.getpass", return_value=CLAVE), patch("sys.stdout", io.StringIO()):
            self.assertEqual(main.main(), 0)
        with patch("sys.argv", ["ecotech", "--crear-admin"]), patch(
            "builtins.input"
        ) as entrada, patch("sys.stdout", io.StringIO()):
            self.assertEqual(main.main(), 1)
        entrada.assert_not_called()
        self.assertEqual(len(UsuarioDAO.listar()), 1)

    def test_informes_del_menu_usan_al_admin_y_las_cuatro_areas(self):
        with patch("sys.stdout", io.StringIO()):
            cargar_semilla()
        admin = UsuarioDAO.buscar_por_nombre("admin_demo")
        with patch("builtins.input", return_value="Desde el menú"), patch(
            "sys.stdout", io.StringIO()
        ):
            menu_informe.generar_informe(main.autenticar(admin.nombre_usuario, "Demo2026*"))
        informe = next(i for i in InformeDAO.listar() if i.tipo == "Desde el menú")
        self.assertEqual(informe.creado_por, admin.id_usuario)
        self.assertIn("Ana Torres", informe._texto_legible())
        self.assertIn("6.50", informe._texto_legible())

    def test_otro_admin_no_recalcula_un_informe_ajeno(self):
        with patch("sys.stdout", io.StringIO()):
            cargar_semilla()
        otro = self.cuenta("otro_admin", admin=True)
        sesion = self.sesion(otro)
        informe = InformeDAO.listar()[0]
        with patch("src.menus.menu_informe.seleccionar_informe", return_value=informe), patch(
            "builtins.input"
        ) as entrada, patch("sys.stdout", io.StringIO()):
            menu_informe.actualizar_informe(sesion)
        entrada.assert_not_called()
        self.assertEqual(InformeDAO.buscar_por_id(informe.id_informe).contenido, informe.contenido)

    def test_semilla_no_restablece_la_contrasena_ya_cambiada(self):
        with patch("sys.stdout", io.StringIO()):
            cargar_semilla()
        usuario = UsuarioDAO.buscar_por_nombre("ana_demo")
        usuario.establecer_contrasena("Personal2026*")
        UsuarioDAO.actualizar(usuario)
        with patch("sys.stdout", io.StringIO()):
            cargar_semilla()
        self.assertIsNone(UsuarioDAO.autenticar("ana_demo", "Demo2026*"))
        self.assertIsNotNone(UsuarioDAO.autenticar("ana_demo", "Personal2026*"))
