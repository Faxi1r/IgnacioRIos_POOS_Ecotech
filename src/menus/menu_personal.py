from datetime import date

from src.servicios import mi_cuenta
from src.servicios.permisos import exigir_sesion
from .comunes import (
    informar,
    mostrar_lista,
    pedir_contrasena,
    pedir_entero,
    pedir_fecha,
    pedir_nombre_empleado,
    pedir_con_validacion,
    pedir_texto,
    submenu,
)
from src.dependencia import Empleado
from .menu_registro import pedir_horas


def ver_mis_datos(sesion):
    empleado = mi_cuenta.mi_ficha(sesion)
    print(empleado)
    print(f"Correo: {empleado.correo}")
    print(
        f"Departamento: {empleado.departamento.nombre if empleado.departamento else 'Sin departamento'}"
    )


def actualizar_mis_datos(sesion):
    exigir_sesion(sesion)
    nombre = pedir_nombre_empleado("Nuevo nombre: ")
    correo = pedir_con_validacion("Nuevo correo: ", Empleado.validar_correo)
    informar(
        mi_cuenta.actualizar_mis_datos(sesion, nombre, correo),
        "Nombre y correo actualizados.",
        "No se encontró su ficha.",
    )


def ver_mis_proyectos(sesion):
    mostrar_lista("Mis proyectos", mi_cuenta.mis_proyectos(sesion))


def ver_mis_horas(sesion):
    mostrar_lista("Mis registros", mi_cuenta.mis_registros(sesion))


def registrar_mis_horas(sesion):
    proyectos = mi_cuenta.mis_proyectos(sesion)
    if not proyectos:
        print("Todavía no tiene proyectos asignados.")
        return
    mostrar_lista("Mis proyectos", proyectos)
    id_proyecto = pedir_entero("Id del proyecto: ")
    if not any(p.id_proyecto == id_proyecto for p in proyectos):
        raise PermissionError("Elija uno de sus proyectos asignados.")
    horas = pedir_horas()
    tareas = pedir_texto("Tareas realizadas: ", "La descripción de tareas", 500)
    fecha = pedir_fecha("Fecha AAAA-MM-DD (Enter para hoy): ", opcional=True) or date.today()
    registro = mi_cuenta.registrar_mis_horas(sesion, id_proyecto, fecha, horas, tareas)
    print(f"Horas guardadas. Id: {registro.id_registro}.")


def cambiar_mi_contrasena(sesion):
    exigir_sesion(sesion)
    mi_cuenta.cambiar_contrasena(sesion, pedir_contrasena())
    print("Contraseña actualizada.")


def menu_personal(sesion):
    submenu(
        "Mi cuenta",
        {
            "1": ("Ver mi ficha", lambda: ver_mis_datos(sesion)),
            "2": ("Cambiar mi nombre y correo", lambda: actualizar_mis_datos(sesion)),
            "3": ("Ver mis proyectos", lambda: ver_mis_proyectos(sesion)),
            "4": ("Ver mis registros", lambda: ver_mis_horas(sesion)),
            "5": ("Registrar mis horas", lambda: registrar_mis_horas(sesion)),
            "6": ("Cambiar mi contraseña", lambda: cambiar_mi_contrasena(sesion)),
        },
        sesion,
        "mi_cuenta",
    )
