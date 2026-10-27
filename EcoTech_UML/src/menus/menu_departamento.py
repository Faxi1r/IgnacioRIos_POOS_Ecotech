from src.dependencia import Departamento
from src.dependencia.validaciones import validar_texto
from src.persistencia import DepartamentoDAO, EmpleadoDAO
from .comunes import (
    confirmar, informar, mostrar_lista, pedir_con_validacion,
    pedir_objeto, pedir_texto, submenu,
)


def seleccionar_departamento():
    return pedir_objeto("Id del departamento: ", DepartamentoDAO.buscar_por_id, "un departamento")


def pedir_gerente(id_departamento=None):
    while True:
        empleado = pedir_objeto("Id del empleado que será gerente: ", EmpleadoDAO.buscar_por_id, "un empleado")
        if empleado.id_departamento not in (None, id_departamento):
            print("Ese empleado pertenece a otro departamento. Elija otro o cambie antes su asignación.")
        else:
            return empleado


def crear_departamento():
    def revisar_nombre(texto):
        nombre = validar_texto(texto, "El nombre del departamento", 100)
        if DepartamentoDAO.buscar_por_nombre(nombre):
            raise ValueError("Ya existe un departamento con ese nombre.")
        return nombre
    nombre = pedir_con_validacion("Nombre del departamento: ", revisar_nombre)
    print("El gerente debe ser un empleado ya registrado y sin departamento.")
    departamento = Departamento(None, nombre, pedir_gerente())
    DepartamentoDAO.insertar(departamento)
    print(f"Departamento registrado correctamente. Id: {departamento.id_departamento}.")


def ver_departamento():
    departamento = seleccionar_departamento()
    print(departamento)
    mostrar_lista("Empleados del departamento", departamento.empleados)


def actualizar_departamento():
    departamento = seleccionar_departamento()
    print(departamento)
    while True:
        nombre = pedir_texto("Nuevo nombre (Enter para mantener): ", "El nombre", opcional=True)
        existente = DepartamentoDAO.buscar_por_nombre(nombre) if nombre else None
        if existente and existente.id_departamento != departamento.id_departamento:
            print("Ya existe otro departamento con ese nombre.")
            continue
        if nombre:
            departamento.nombre = nombre
        break
    if confirmar("¿Cambiar al gerente?"):
        departamento.asignar_gerente(pedir_gerente(departamento.id_departamento))
    informar(DepartamentoDAO.actualizar(departamento), "Departamento actualizado.", "El departamento ya no existe.")


def agregar_a_departamento():
    departamento = seleccionar_departamento()
    empleado = pedir_objeto("Id del empleado: ", EmpleadoDAO.buscar_por_id, "un empleado")
    informar(DepartamentoDAO.agregar_empleado(departamento.id_departamento, empleado.id_empleado),
             "Empleado asignado al departamento.", "El empleado ya no existe.")


def quitar_de_departamento():
    departamento = seleccionar_departamento()
    empleado = pedir_objeto("Id del empleado: ", EmpleadoDAO.buscar_por_id, "un empleado")
    if confirmar("¿Quitar al empleado? Si es gerente, debe reemplazarlo primero"):
        informar(DepartamentoDAO.quitar_empleado(departamento.id_departamento, empleado.id_empleado),
                 "Empleado quitado del departamento.", "Ese empleado no pertenece al departamento.")


def cambiar_de_departamento():
    empleado = pedir_objeto("Id del empleado: ", EmpleadoDAO.buscar_por_id, "un empleado")
    departamento = seleccionar_departamento()
    if confirmar(f"¿Asignar a {empleado.nombre} a {departamento.nombre}?"):
        informar(DepartamentoDAO.reasignar_empleado(empleado.id_empleado, departamento.id_departamento),
                 "Departamento del empleado actualizado.", "El empleado ya no existe.")


def eliminar_departamento():
    departamento = seleccionar_departamento()
    if confirmar(f"¿Eliminar {departamento.nombre}? Sus empleados no se borrarán"):
        informar(DepartamentoDAO.eliminar(departamento.id_departamento), "Departamento eliminado.", "El departamento ya no existe.")


def menu_departamento(usuario):
    submenu("Departamentos", {
        "1": ("Crear con su gerente", crear_departamento),
        "2": ("Listar", lambda: mostrar_lista("Departamentos", DepartamentoDAO.listar())),
        "3": ("Ver gerente y empleados", ver_departamento),
        "4": ("Actualizar nombre o gerente", actualizar_departamento),
        "5": ("Agregar empleado", agregar_a_departamento),
        "6": ("Quitar empleado", quitar_de_departamento),
        "7": ("Eliminar", eliminar_departamento),
        "8": ("Cambiar a un empleado de departamento", cambiar_de_departamento),
    }, usuario, "departamentos")
