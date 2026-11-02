from datetime import date

from src.persistencia import DAOError, EmpleadoDAO, ProyectoDAO, RegistroTiempoDAO
from .comunes import (
    confirmar, informar, mostrar_lista, pedir_fecha, pedir_numero, pedir_objeto,
    pedir_texto, submenu,
)


def pedir_horas():
    return pedir_numero("Horas trabajadas: ", "Las horas", minimo=0, maximo=24,
                       minimo_exclusivo=True, decimales=2)


def registrar_horas():
    empleado = pedir_objeto("Id del empleado: ", EmpleadoDAO.buscar_por_id, "un empleado")
    registrar_para_empleado(empleado)


def registrar_para_empleado(empleado):
    proyectos = [proyecto for proyecto in ProyectoDAO.listar() if empleado in proyecto.empleados_asignados]
    if not proyectos:
        print("El empleado todavía no tiene proyectos asignados.")
        return
    mostrar_lista("Proyectos del empleado", proyectos)
    while True:
        proyecto = pedir_objeto("Id del proyecto: ", ProyectoDAO.buscar_por_id, "un proyecto")
        if empleado in proyecto.empleados_asignados:
            break
        print("El empleado no está asignado a ese proyecto. Elija otro o cancele y asígnelo desde Proyectos.")
    while True:
        horas = pedir_horas()
        tareas = pedir_texto("Tareas realizadas: ", "La descripción de tareas", 500)
        fecha = pedir_fecha("Fecha AAAA-MM-DD (Enter para hoy): ", opcional=True) or date.today()
        registro = empleado.registrar_horas(fecha, proyecto, horas, tareas)
        try:
            RegistroTiempoDAO.insertar(registro)
            print(f"Horas guardadas correctamente. Id del registro: {registro.id_registro}.")
            return
        except DAOError as error:
            print(f"No se guardó el registro: {error}")
            if not confirmar("¿Volver a ingresar horas, tareas y fecha para este empleado y proyecto?"):
                return
            # Volvemos a cargar lo guardado antes de intentar otra vez.
            empleado = EmpleadoDAO.buscar_por_id(empleado.id_empleado)
            proyecto = ProyectoDAO.buscar_por_id(proyecto.id_proyecto)


def buscar_registro():
    print(pedir_objeto("Id del registro: ", RegistroTiempoDAO.buscar_por_id, "un registro"))


def horas_de_empleado():
    empleado = pedir_objeto("Id del empleado: ", EmpleadoDAO.buscar_por_id, "un empleado")
    mostrar_lista("Horas del empleado", empleado.registros_tiempo)


def actualizar_registro():
    registro = pedir_objeto("Id del registro: ", RegistroTiempoDAO.buscar_por_id, "un registro")
    print(registro)
    while True:
        registro.horas = pedir_horas()
        registro.descripcion_tareas = pedir_texto("Nueva descripción: ", "La descripción de tareas", 500)
        registro.fecha = pedir_fecha("Nueva fecha AAAA-MM-DD (Enter para mantener): ", opcional=True) or registro.fecha
        try:
            informar(RegistroTiempoDAO.actualizar(registro), "Registro actualizado.", "El registro ya no existe.")
            return
        except DAOError as error:
            print(f"No se guardaron los cambios: {error}")
            if not confirmar("¿Corregir nuevamente los datos del registro?"):
                return


def eliminar_registro():
    registro = pedir_objeto("Id del registro: ", RegistroTiempoDAO.buscar_por_id, "un registro")
    if confirmar(f"¿Eliminar el registro {registro.id_registro}, de {registro.horas} horas?"):
        informar(RegistroTiempoDAO.eliminar(registro.id_registro), "Registro eliminado.", "El registro ya no existe.")


def menu_registro(usuario):
    submenu("Registro de horas", {
        "1": ("Registrar horas", registrar_horas),
        "2": ("Listar registros", lambda: mostrar_lista("Registros", RegistroTiempoDAO.listar())),
        "3": ("Buscar por id", buscar_registro),
        "4": ("Ver horas por empleado", horas_de_empleado),
        "5": ("Actualizar", actualizar_registro),
        "6": ("Eliminar", eliminar_registro),
    }, usuario, "registros")
