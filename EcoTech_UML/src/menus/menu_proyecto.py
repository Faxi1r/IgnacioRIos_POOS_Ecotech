from src.dependencia import Proyecto
from src.dependencia.validaciones import validar_texto
from src.persistencia import EmpleadoDAO, ProyectoDAO
from .comunes import (
    confirmar, informar, mostrar_lista, pedir_con_validacion, pedir_fecha,
    pedir_objeto, pedir_texto, submenu,
)


def seleccionar_proyecto():
    return pedir_objeto("Id del proyecto: ", ProyectoDAO.buscar_por_id, "un proyecto")


def pedir_nombre(id_actual=None):
    def revisar(texto):
        nombre = validar_texto(texto, "El nombre del proyecto", 150)
        existente = ProyectoDAO.buscar_por_nombre(nombre)
        if existente and existente.id_proyecto != id_actual:
            raise ValueError("Ya existe un proyecto con ese nombre. Ingrese otro.")
        return nombre
    return pedir_con_validacion("Nombre del proyecto: ", revisar)


def crear_proyecto():
    proyecto = Proyecto(None, pedir_nombre(),
                        pedir_texto("Descripción: ", "La descripción del proyecto", 500),
                        pedir_fecha("Fecha de inicio AAAA-MM-DD: "))
    ProyectoDAO.insertar(proyecto)
    print(f"Proyecto registrado correctamente. Id: {proyecto.id_proyecto}.")


def ver_proyecto():
    proyecto = seleccionar_proyecto()
    print(proyecto)
    mostrar_lista("Empleados asignados", proyecto.empleados_asignados)
    mostrar_lista("Horas guardadas", proyecto.registros_tiempo)
    print(f"Horas totales: {sum(r.horas for r in proyecto.registros_tiempo):.2f}")


def actualizar_proyecto():
    proyecto = seleccionar_proyecto()
    print(proyecto)
    if confirmar("¿Cambiar el nombre?"):
        proyecto.nombre = pedir_nombre(proyecto.id_proyecto)
    descripcion = pedir_texto("Nueva descripción (Enter para mantener): ", "La descripción", 500, opcional=True)
    fecha = pedir_fecha("Nueva fecha AAAA-MM-DD (Enter para mantener): ", opcional=True)
    if descripcion:
        proyecto.descripcion = descripcion
    if fecha:
        proyecto.fecha_inicio = fecha
    informar(ProyectoDAO.actualizar(proyecto), "Proyecto actualizado.", "El proyecto ya no existe.")


def asignar_a_proyecto():
    proyecto = seleccionar_proyecto()
    empleado = pedir_objeto("Id del empleado: ", EmpleadoDAO.buscar_por_id, "un empleado")
    informar(ProyectoDAO.asignar_empleado(proyecto.id_proyecto, empleado.id_empleado),
             "Empleado asignado al proyecto.", "El empleado ya estaba asignado a ese proyecto.")


def desasignar_de_proyecto():
    proyecto = seleccionar_proyecto()
    empleado = pedir_objeto("Id del empleado: ", EmpleadoDAO.buscar_por_id, "un empleado")
    if confirmar("¿Quitar la asignación? Las horas anteriores se conservarán"):
        informar(ProyectoDAO.desasignar_empleado(proyecto.id_proyecto, empleado.id_empleado),
                 "Empleado desasignado.", "El empleado no estaba asignado a ese proyecto.")


def eliminar_proyecto():
    proyecto = seleccionar_proyecto()
    if confirmar(f"¿Eliminar {proyecto.nombre}? Solo se permite si no tiene horas guardadas"):
        informar(ProyectoDAO.eliminar(proyecto.id_proyecto), "Proyecto eliminado.", "El proyecto ya no existe.")


def menu_proyecto(usuario):
    submenu("Proyectos", {
        "1": ("Crear", crear_proyecto),
        "2": ("Listar", lambda: mostrar_lista("Proyectos", ProyectoDAO.listar())),
        "3": ("Ver empleados y horas", ver_proyecto),
        "4": ("Actualizar", actualizar_proyecto),
        "5": ("Asignar empleado", asignar_a_proyecto),
        "6": ("Desasignar empleado", desasignar_de_proyecto),
        "7": ("Eliminar", eliminar_proyecto),
    }, usuario, "proyectos")
