from src.persistencia import EmpleadoDAO
from .permisos import exigir_admin


def insertar(sesion, empleado):
    exigir_admin(sesion)
    return EmpleadoDAO.insertar(empleado)


def buscar_por_id(sesion, id_empleado):
    exigir_admin(sesion)
    return EmpleadoDAO.buscar_por_id(id_empleado)


def buscar_por_identificacion(sesion, identificacion):
    exigir_admin(sesion)
    return EmpleadoDAO.buscar_por_identificacion(identificacion)


def buscar_por_correo(sesion, correo):
    exigir_admin(sesion)
    return EmpleadoDAO.buscar_por_correo(correo)


def listar_todos(sesion):
    exigir_admin(sesion)
    return EmpleadoDAO.listar()


def actualizar(sesion, empleado):
    exigir_admin(sesion)
    return EmpleadoDAO.actualizar(empleado)


def vincular_cuenta(sesion, id_empleado, id_usuario):
    exigir_admin(sesion)
    return EmpleadoDAO.vincular_cuenta(id_empleado, id_usuario)


def desvincular_cuenta(sesion, id_empleado):
    exigir_admin(sesion)
    if id_empleado == sesion["empleado_id"]:
        raise PermissionError("No puede quitar el empleado de su propia sesión.")
    return EmpleadoDAO.desvincular_cuenta(id_empleado)


def eliminar(sesion, id_empleado):
    exigir_admin(sesion)
    if id_empleado == sesion["empleado_id"]:
        raise PermissionError("No puede quitar el empleado de su propia sesión.")
    return EmpleadoDAO.eliminar(id_empleado)
