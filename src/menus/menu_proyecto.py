from src.servicios.permisos import exigir_admin
from src.dependencia import Proyecto
from src.dependencia.validaciones import validar_texto
from src.servicios import gestion_empleados, gestion_proyectos
from .comunes import (
    confirmar,
    informar,
    mostrar_lista,
    pedir_con_validacion,
    pedir_fecha,
    pedir_objeto,
    pedir_texto,
    submenu,
)


def seleccionar_proyecto(sesion):
    exigir_admin(sesion)
    return pedir_objeto(
        "Id del proyecto: ",
        lambda identificador: gestion_proyectos.buscar_por_id(sesion, identificador),
        "un proyecto",
    )


def pedir_nombre(sesion, id_actual=None):
    exigir_admin(sesion)

    def revisar(texto):
        nombre = validar_texto(texto, "El nombre del proyecto", 150)
        existente = gestion_proyectos.buscar_por_nombre(sesion, nombre)
        if existente and existente.id_proyecto != id_actual:
            raise ValueError("Ya existe un proyecto con ese nombre. Ingrese otro.")
        return nombre

    return pedir_con_validacion("Nombre del proyecto: ", revisar)


def crear_proyecto(sesion):
    exigir_admin(sesion)
    proyecto = Proyecto(
        None,
        pedir_nombre(sesion),
        pedir_texto("Descripción: ", "La descripción del proyecto", 500),
        pedir_fecha("Fecha de inicio AAAA-MM-DD: "),
    )
    gestion_proyectos.insertar(sesion, proyecto)
    print(f"Proyecto registrado correctamente. Id: {proyecto.id_proyecto}.")


def ver_proyecto(sesion):
    exigir_admin(sesion)
    proyecto = seleccionar_proyecto(sesion)
    print(proyecto)
    mostrar_lista("Empleados asignados", proyecto.empleados_asignados)
    mostrar_lista("Horas guardadas", proyecto.registros_tiempo)
    print(f"Horas totales: {sum((r.horas for r in proyecto.registros_tiempo)):.2f}")


def actualizar_proyecto(sesion):
    exigir_admin(sesion)
    proyecto = seleccionar_proyecto(sesion)
    print(proyecto)
    if confirmar("¿Cambiar el nombre?"):
        proyecto.nombre = pedir_nombre(sesion, proyecto.id_proyecto)
    descripcion = pedir_texto(
        "Nueva descripción (Enter para mantener): ", "La descripción", 500, opcional=True
    )
    fecha = pedir_fecha("Nueva fecha AAAA-MM-DD (Enter para mantener): ", opcional=True)
    if descripcion:
        proyecto.descripcion = descripcion
    if fecha:
        proyecto.fecha_inicio = fecha
    informar(
        gestion_proyectos.actualizar(sesion, proyecto),
        "Proyecto actualizado.",
        "El proyecto ya no existe.",
    )


def asignar_a_proyecto(sesion):
    exigir_admin(sesion)
    proyecto = seleccionar_proyecto(sesion)
    empleado = pedir_objeto(
        "Id del empleado: ",
        lambda identificador: gestion_empleados.buscar_por_id(sesion, identificador),
        "un empleado",
    )
    informar(
        gestion_proyectos.asignar_empleado(sesion, proyecto.id_proyecto, empleado.id_empleado),
        "Empleado asignado al proyecto.",
        "El empleado ya estaba asignado a ese proyecto.",
    )


def desasignar_de_proyecto(sesion):
    exigir_admin(sesion)
    proyecto = seleccionar_proyecto(sesion)
    empleado = pedir_objeto(
        "Id del empleado: ",
        lambda identificador: gestion_empleados.buscar_por_id(sesion, identificador),
        "un empleado",
    )
    if confirmar("¿Quitar la asignación? Las horas anteriores se conservarán"):
        informar(
            gestion_proyectos.desasignar_empleado(
                sesion, proyecto.id_proyecto, empleado.id_empleado
            ),
            "Empleado desasignado.",
            "El empleado no estaba asignado a ese proyecto.",
        )


def eliminar_proyecto(sesion):
    exigir_admin(sesion)
    proyecto = seleccionar_proyecto(sesion)
    if confirmar(f"¿Eliminar {proyecto.nombre}? Solo se permite si no tiene horas guardadas"):
        informar(
            gestion_proyectos.eliminar(sesion, proyecto.id_proyecto),
            "Proyecto eliminado.",
            "El proyecto ya no existe.",
        )


def menu_proyecto(sesion):
    exigir_admin(sesion)
    submenu(
        "Proyectos",
        {
            "1": ("Crear", lambda: crear_proyecto(sesion)),
            "2": ("Listar", lambda: mostrar_lista("Proyectos", gestion_proyectos.listar(sesion))),
            "3": ("Ver empleados y horas", lambda: ver_proyecto(sesion)),
            "4": ("Actualizar", lambda: actualizar_proyecto(sesion)),
            "5": ("Asignar empleado", lambda: asignar_a_proyecto(sesion)),
            "6": ("Desasignar empleado", lambda: desasignar_de_proyecto(sesion)),
            "7": ("Eliminar", lambda: eliminar_proyecto(sesion)),
        },
        sesion,
        "proyectos",
    )
