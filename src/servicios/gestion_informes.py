from src.persistencia import (
    DepartamentoDAO,
    EmpleadoDAO,
    InformeDAO,
    ProyectoDAO,
    RegistroTiempoDAO,
    UsuarioDAO,
)
from .permisos import exigir_admin


def generar(sesion, tipo):
    exigir_admin(sesion)
    admin = UsuarioDAO.buscar_por_id(sesion["id"])
    informe = admin.generar_informe(
        tipo,
        EmpleadoDAO.listar(),
        DepartamentoDAO.listar(),
        ProyectoDAO.listar(),
        RegistroTiempoDAO.listar(),
    )
    return InformeDAO.insertar(informe)


def listar(sesion):
    exigir_admin(sesion)
    return InformeDAO.listar()


def buscar_por_id(sesion, id_informe):
    exigir_admin(sesion)
    return InformeDAO.buscar_por_id(id_informe)


def recalcular(sesion, id_informe, tipo):
    exigir_admin(sesion)
    anterior = InformeDAO.buscar_por_id(id_informe)
    if anterior is None:
        raise ValueError("El informe ya no existe.")
    if anterior.creado_por != sesion["id"]:
        raise PermissionError("Solo el autor puede recalcular su informe.")
    admin = UsuarioDAO.buscar_por_id(sesion["id"])
    informe = admin.generar_informe(
        tipo,
        EmpleadoDAO.listar(),
        DepartamentoDAO.listar(),
        ProyectoDAO.listar(),
        RegistroTiempoDAO.listar(),
    )
    informe.id_informe = id_informe
    return InformeDAO.actualizar(informe)


def exportar(sesion, id_informe, ruta, extension):
    exigir_admin(sesion)
    informe = InformeDAO.buscar_por_id(id_informe)
    if informe is None:
        raise ValueError("El informe ya no existe.")
    if extension == ".pdf":
        informe.exportar_pdf(str(ruta))
    elif extension == ".xlsx":
        informe.exportar_excel(str(ruta))
    else:
        raise ValueError("Elija PDF o Excel.")


def eliminar(sesion, id_informe):
    exigir_admin(sesion)
    return InformeDAO.eliminar(id_informe)
