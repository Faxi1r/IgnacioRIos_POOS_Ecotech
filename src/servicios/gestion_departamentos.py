from src.persistencia import DepartamentoDAO
from .permisos import exigir_admin


def insertar(sesion, departamento):
    exigir_admin(sesion)
    return DepartamentoDAO.insertar(departamento)


def buscar_por_id(sesion, id_departamento):
    exigir_admin(sesion)
    return DepartamentoDAO.buscar_por_id(id_departamento)


def buscar_por_nombre(sesion, nombre):
    exigir_admin(sesion)
    return DepartamentoDAO.buscar_por_nombre(nombre)


def listar(sesion):
    exigir_admin(sesion)
    return DepartamentoDAO.listar()


def actualizar(sesion, departamento):
    exigir_admin(sesion)
    return DepartamentoDAO.actualizar(departamento)


def agregar_empleado(sesion, id_departamento, id_empleado):
    exigir_admin(sesion)
    return DepartamentoDAO.agregar_empleado(id_departamento, id_empleado)


def quitar_empleado(sesion, id_departamento, id_empleado):
    exigir_admin(sesion)
    return DepartamentoDAO.quitar_empleado(id_departamento, id_empleado)


def reasignar_empleado(sesion, id_empleado, id_destino):
    exigir_admin(sesion)
    return DepartamentoDAO.reasignar_empleado(id_empleado, id_destino)


def eliminar(sesion, id_departamento):
    exigir_admin(sesion)
    return DepartamentoDAO.eliminar(id_departamento)
