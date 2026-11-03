"""Preparación inicial desde la terminal, fuera de los menús autenticados."""

from src.dependencia import Administrador
from src.persistencia import EmpleadoDAO, UsuarioDAO


def crear_admin_inicial(nombre_usuario, contrasena, empleado):
    if UsuarioDAO.hay_administradores():
        raise PermissionError("Ya existe un administrador. Use el inicio de sesión.")
    cuenta = Administrador(None, nombre_usuario, rol="admin")
    cuenta.establecer_contrasena(contrasena)
    if UsuarioDAO.buscar_por_nombre(cuenta.nombre_usuario) is not None:
        raise ValueError("El nombre de usuario ya existe.")
    if empleado.id_empleado is None:
        EmpleadoDAO.insertar(empleado)
    return UsuarioDAO.insertar_vinculado(cuenta, empleado.id_empleado)
