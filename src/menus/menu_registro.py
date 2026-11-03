from src.servicios.permisos import exigir_admin
from datetime import date
from src.persistencia import DAOError
from src.servicios import gestion_empleados, gestion_proyectos, gestion_registros
from .comunes import (
    confirmar,
    informar,
    mostrar_lista,
    pedir_fecha,
    pedir_numero,
    pedir_objeto,
    pedir_texto,
    submenu,
)


def pedir_horas():
    return pedir_numero(
        "Horas trabajadas: ", "Las horas", minimo=0, maximo=24, minimo_exclusivo=True, decimales=2
    )


def registrar_horas(sesion):
    exigir_admin(sesion)
    empleado = pedir_objeto(
        "Id del empleado: ",
        lambda identificador: gestion_empleados.buscar_por_id(sesion, identificador),
        "un empleado",
    )
    registrar_para_empleado(sesion, empleado)


def registrar_para_empleado(sesion, empleado):
    exigir_admin(sesion)
    proyectos = [
        proyecto
        for proyecto in gestion_proyectos.listar(sesion)
        if empleado in proyecto.empleados_asignados
    ]
    if not proyectos:
        print("El empleado todavía no tiene proyectos asignados.")
        return
    mostrar_lista("Proyectos del empleado", proyectos)
    while True:
        proyecto = pedir_objeto(
            "Id del proyecto: ",
            lambda identificador: gestion_proyectos.buscar_por_id(sesion, identificador),
            "un proyecto",
        )
        if empleado in proyecto.empleados_asignados:
            break
        print(
            "El empleado no está asignado a ese proyecto. Elija otro o cancele y asígnelo desde Proyectos."
        )
    while True:
        horas = pedir_horas()
        tareas = pedir_texto("Tareas realizadas: ", "La descripción de tareas", 500)
        fecha = pedir_fecha("Fecha AAAA-MM-DD (Enter para hoy): ", opcional=True) or date.today()
        registro = empleado.registrar_horas(fecha, proyecto, horas, tareas)
        try:
            gestion_registros.insertar(sesion, registro)
            print(f"Horas guardadas correctamente. Id del registro: {registro.id_registro}.")
            return
        except DAOError as error:
            print(f"No se guardó el registro: {error}")
            if not confirmar(
                "¿Volver a ingresar horas, tareas y fecha para este empleado y proyecto?"
            ):
                return
            empleado = gestion_empleados.buscar_por_id(sesion, empleado.id_empleado)
            proyecto = gestion_proyectos.buscar_por_id(sesion, proyecto.id_proyecto)


def buscar_registro(sesion):
    exigir_admin(sesion)
    print(
        pedir_objeto(
            "Id del registro: ",
            lambda identificador: gestion_registros.buscar_por_id(sesion, identificador),
            "un registro",
        )
    )


def horas_de_empleado(sesion):
    exigir_admin(sesion)
    empleado = pedir_objeto(
        "Id del empleado: ",
        lambda identificador: gestion_empleados.buscar_por_id(sesion, identificador),
        "un empleado",
    )
    mostrar_lista("Horas del empleado", empleado.registros_tiempo)


def actualizar_registro(sesion):
    exigir_admin(sesion)
    registro = pedir_objeto(
        "Id del registro: ",
        lambda identificador: gestion_registros.buscar_por_id(sesion, identificador),
        "un registro",
    )
    print(registro)
    while True:
        registro.horas = pedir_horas()
        registro.descripcion_tareas = pedir_texto(
            "Nueva descripción: ", "La descripción de tareas", 500
        )
        registro.fecha = (
            pedir_fecha("Nueva fecha AAAA-MM-DD (Enter para mantener): ", opcional=True)
            or registro.fecha
        )
        try:
            informar(
                gestion_registros.actualizar(sesion, registro),
                "Registro actualizado.",
                "El registro ya no existe.",
            )
            return
        except DAOError as error:
            print(f"No se guardaron los cambios: {error}")
            if not confirmar("¿Corregir nuevamente los datos del registro?"):
                return


def eliminar_registro(sesion):
    exigir_admin(sesion)
    registro = pedir_objeto(
        "Id del registro: ",
        lambda identificador: gestion_registros.buscar_por_id(sesion, identificador),
        "un registro",
    )
    if confirmar(f"¿Eliminar el registro {registro.id_registro}, de {registro.horas} horas?"):
        informar(
            gestion_registros.eliminar(sesion, registro.id_registro),
            "Registro eliminado.",
            "El registro ya no existe.",
        )


def menu_registro(sesion):
    exigir_admin(sesion)
    submenu(
        "Registro de horas",
        {
            "1": ("Registrar horas", lambda: registrar_horas(sesion)),
            "2": (
                "Listar registros",
                lambda: mostrar_lista("Registros", gestion_registros.listar(sesion)),
            ),
            "3": ("Buscar por id", lambda: buscar_registro(sesion)),
            "4": ("Ver horas por empleado", lambda: horas_de_empleado(sesion)),
            "5": ("Actualizar", lambda: actualizar_registro(sesion)),
            "6": ("Eliminar", lambda: eliminar_registro(sesion)),
        },
        sesion,
        "registros",
    )
