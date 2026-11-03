from src.persistencia import ProyectoDAO
from .permisos import exigir_admin


def buscar_por_nombre(sesion, nombre):
    exigir_admin(sesion)
    return ProyectoDAO.buscar_por_nombre(nombre)


def insertar(sesion, proyecto):
    exigir_admin(sesion)
    return ProyectoDAO.insertar(proyecto)


def buscar_por_id(sesion, id_proyecto):
    exigir_admin(sesion)
    return ProyectoDAO.buscar_por_id(id_proyecto)


def listar(sesion):
    exigir_admin(sesion)
    return ProyectoDAO.listar()


def actualizar(sesion, proyecto):
    exigir_admin(sesion)
    return ProyectoDAO.actualizar(proyecto)


def eliminar(sesion, id_proyecto):
    exigir_admin(sesion)
    return ProyectoDAO.eliminar(id_proyecto)


def asignar_empleado(sesion, id_proyecto, id_empleado):
    exigir_admin(sesion)
    return ProyectoDAO.asignar_empleado(id_proyecto, id_empleado)


def desasignar_empleado(sesion, id_proyecto, id_empleado):
    exigir_admin(sesion)
    return ProyectoDAO.desasignar_empleado(id_proyecto, id_empleado)
