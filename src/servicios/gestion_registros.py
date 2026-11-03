from src.persistencia import RegistroTiempoDAO
from .permisos import exigir_admin


def insertar(sesion, registro):
    exigir_admin(sesion)
    return RegistroTiempoDAO.insertar(registro)


def buscar_por_id(sesion, id_registro):
    exigir_admin(sesion)
    return RegistroTiempoDAO.buscar_por_id(id_registro)


def listar(sesion):
    exigir_admin(sesion)
    return RegistroTiempoDAO.listar()


def listar_por_empleado(sesion, id_empleado):
    exigir_admin(sesion)
    return RegistroTiempoDAO.listar_por_empleado(id_empleado)


def actualizar(sesion, registro):
    exigir_admin(sesion)
    return RegistroTiempoDAO.actualizar(registro)


def eliminar(sesion, id_registro):
    exigir_admin(sesion)
    return RegistroTiempoDAO.eliminar(id_registro)
