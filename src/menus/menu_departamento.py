from src.servicios.permisos import exigir_admin
from src.dependencia import Departamento
from src.dependencia.validaciones import validar_texto
from src.servicios import gestion_departamentos, gestion_empleados
from .comunes import (
    confirmar,
    informar,
    mostrar_lista,
    pedir_con_validacion,
    pedir_objeto,
    pedir_texto,
    submenu,
)


def seleccionar_departamento(sesion):
    exigir_admin(sesion)
    return pedir_objeto(
        "Id del departamento: ",
        lambda identificador: gestion_departamentos.buscar_por_id(sesion, identificador),
        "un departamento",
    )


def pedir_gerente(sesion, id_departamento=None):
    exigir_admin(sesion)
    while True:
        empleado = pedir_objeto(
            "Id del empleado que será gerente: ",
            lambda identificador: gestion_empleados.buscar_por_id(sesion, identificador),
            "un empleado",
        )
        if empleado.id_departamento not in (None, id_departamento):
            print(
                "Ese empleado pertenece a otro departamento. Elija otro o cambie antes su asignación."
            )
        else:
            return empleado


def crear_departamento(sesion):
    exigir_admin(sesion)

    def revisar_nombre(texto):
        nombre = validar_texto(texto, "El nombre del departamento", 100)
        if gestion_departamentos.buscar_por_nombre(sesion, nombre):
            raise ValueError("Ya existe un departamento con ese nombre.")
        return nombre

    nombre = pedir_con_validacion("Nombre del departamento: ", revisar_nombre)
    print("El gerente debe ser un empleado ya registrado y sin departamento.")
    departamento = Departamento(None, nombre, pedir_gerente(sesion))
    gestion_departamentos.insertar(sesion, departamento)
    print(f"Departamento registrado correctamente. Id: {departamento.id_departamento}.")


def ver_departamento(sesion):
    exigir_admin(sesion)
    departamento = seleccionar_departamento(sesion)
    print(departamento)
    mostrar_lista("Empleados del departamento", departamento.empleados)


def actualizar_departamento(sesion):
    exigir_admin(sesion)
    departamento = seleccionar_departamento(sesion)
    print(departamento)
    while True:
        nombre = pedir_texto("Nuevo nombre (Enter para mantener): ", "El nombre", opcional=True)
        existente = gestion_departamentos.buscar_por_nombre(sesion, nombre) if nombre else None
        if existente and existente.id_departamento != departamento.id_departamento:
            print("Ya existe otro departamento con ese nombre.")
            continue
        if nombre:
            departamento.nombre = nombre
        break
    if confirmar("¿Cambiar al gerente?"):
        departamento.asignar_gerente(pedir_gerente(sesion, departamento.id_departamento))
    informar(
        gestion_departamentos.actualizar(sesion, departamento),
        "Departamento actualizado.",
        "El departamento ya no existe.",
    )


def agregar_a_departamento(sesion):
    exigir_admin(sesion)
    departamento = seleccionar_departamento(sesion)
    empleado = pedir_objeto(
        "Id del empleado: ",
        lambda identificador: gestion_empleados.buscar_por_id(sesion, identificador),
        "un empleado",
    )
    informar(
        gestion_departamentos.agregar_empleado(
            sesion, departamento.id_departamento, empleado.id_empleado
        ),
        "Empleado asignado al departamento.",
        "El empleado ya no existe.",
    )


def quitar_de_departamento(sesion):
    exigir_admin(sesion)
    departamento = seleccionar_departamento(sesion)
    empleado = pedir_objeto(
        "Id del empleado: ",
        lambda identificador: gestion_empleados.buscar_por_id(sesion, identificador),
        "un empleado",
    )
    if confirmar("¿Quitar al empleado? Si es gerente, debe reemplazarlo primero"):
        informar(
            gestion_departamentos.quitar_empleado(
                sesion, departamento.id_departamento, empleado.id_empleado
            ),
            "Empleado quitado del departamento.",
            "Ese empleado no pertenece al departamento.",
        )


def cambiar_de_departamento(sesion):
    exigir_admin(sesion)
    empleado = pedir_objeto(
        "Id del empleado: ",
        lambda identificador: gestion_empleados.buscar_por_id(sesion, identificador),
        "un empleado",
    )
    departamento = seleccionar_departamento(sesion)
    if confirmar(f"¿Asignar a {empleado.nombre} a {departamento.nombre}?"):
        informar(
            gestion_departamentos.reasignar_empleado(
                sesion, empleado.id_empleado, departamento.id_departamento
            ),
            "Departamento del empleado actualizado.",
            "El empleado ya no existe.",
        )


def eliminar_departamento(sesion):
    exigir_admin(sesion)
    departamento = seleccionar_departamento(sesion)
    if confirmar(f"¿Eliminar {departamento.nombre}? Sus empleados no se borrarán"):
        informar(
            gestion_departamentos.eliminar(sesion, departamento.id_departamento),
            "Departamento eliminado.",
            "El departamento ya no existe.",
        )


def menu_departamento(sesion):
    exigir_admin(sesion)
    submenu(
        "Departamentos",
        {
            "1": ("Crear con su gerente", lambda: crear_departamento(sesion)),
            "2": (
                "Listar",
                lambda: mostrar_lista("Departamentos", gestion_departamentos.listar(sesion)),
            ),
            "3": ("Ver gerente y empleados", lambda: ver_departamento(sesion)),
            "4": ("Actualizar nombre o gerente", lambda: actualizar_departamento(sesion)),
            "5": ("Agregar empleado", lambda: agregar_a_departamento(sesion)),
            "6": ("Quitar empleado", lambda: quitar_de_departamento(sesion)),
            "7": ("Eliminar", lambda: eliminar_departamento(sesion)),
            "8": ("Cambiar a un empleado de departamento", lambda: cambiar_de_departamento(sesion)),
        },
        sesion,
        "departamentos",
    )
