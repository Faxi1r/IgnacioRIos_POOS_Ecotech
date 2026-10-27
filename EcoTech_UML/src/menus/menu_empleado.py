from src.dependencia import Empleado
from src.dependencia.validaciones import validar_telefono, validar_texto
from src.persistencia import EmpleadoDAO, UsuarioDAO
from .comunes import (
    confirmar, informar, mostrar_lista, pedir_con_validacion,
    pedir_correo_nuevo, pedir_fecha, pedir_identificacion_nueva, pedir_numero,
    pedir_objeto, pedir_texto, pedir_nombre_empleado, submenu,
)


def seleccionar_empleado():
    return pedir_objeto("Id del empleado: ", EmpleadoDAO.buscar_por_id, "un empleado")


def pedir_telefono():
    return pedir_con_validacion("Teléfono: ", lambda valor: validar_telefono(
        validar_texto(valor, "El teléfono", 20)))


def registrar_empleado():
    empleado = Empleado(
        None, pedir_identificacion_nueva(), pedir_nombre_empleado(),
        pedir_correo_nuevo(),
        pedir_numero("Salario, sin separador de miles: ", "El salario",
                     minimo=0, maximo=9999999999.99, decimales=2),
        pedir_texto("Dirección: ", "La dirección", 255), pedir_telefono(),
        pedir_fecha("Inicio del contrato AAAA-MM-DD: "),
    )
    EmpleadoDAO.insertar(empleado)
    print(f"Empleado registrado correctamente. Id: {empleado.id_empleado}.")


def buscar_empleado():
    empleado = seleccionar_empleado()
    print(empleado)
    print(f"Correo: {empleado.correo} | Teléfono: {empleado.telefono}")
    print(f"Dirección: {empleado.direccion}")
    print(f"Contrato: {empleado.fecha_inicio_contrato} | Salario: {empleado.salario:.2f}")
    print(f"Departamento: {empleado.departamento.nombre if empleado.departamento else 'Sin departamento'}")
    print(f"Cuenta: {empleado.usuario.nombre_usuario if empleado.usuario else 'Sin cuenta'}")
    mostrar_lista("Horas guardadas del empleado", empleado.registros_tiempo)


def actualizar_empleado():
    empleado = seleccionar_empleado()
    print(empleado)
    if confirmar("¿Corregir la identificación?"):
        empleado.identificacion = pedir_identificacion_nueva(empleado.id_empleado)
    nombre = pedir_nombre_empleado("Nuevo nombre (Enter para mantener): ", opcional=True)
    salario = pedir_numero("Nuevo salario (Enter para mantener): ", "El salario", opcional=True,
                          minimo=0, maximo=9999999999.99, decimales=2)
    if nombre:
        empleado.nombre = nombre
    if salario is not None:
        empleado.salario = salario
    if confirmar("¿Cambiar el correo?"):
        empleado.correo = pedir_correo_nuevo(empleado.id_empleado)
    if confirmar("¿Cambiar la dirección?"):
        empleado.direccion = pedir_texto("Nueva dirección: ", "La dirección", 255)
    if confirmar("¿Cambiar el teléfono?"):
        empleado.telefono = pedir_telefono()
    if confirmar("¿Cambiar la fecha de contrato?"):
        empleado.fecha_inicio_contrato = pedir_fecha("Nueva fecha AAAA-MM-DD: ")
    informar(EmpleadoDAO.actualizar(empleado), "Empleado actualizado.", "El empleado ya no existe.")


def vincular_cuenta():
    empleado = seleccionar_empleado()
    usuario = pedir_objeto("Id de la cuenta: ", UsuarioDAO.buscar_por_id, "una cuenta")
    informar(EmpleadoDAO.vincular_cuenta(empleado.id_empleado, usuario.id_usuario),
             "Cuenta vinculada al empleado.", "El empleado ya no existe.")


def desvincular_cuenta():
    empleado = seleccionar_empleado()
    if empleado.usuario is None:
        print("El empleado no tiene una cuenta vinculada.")
        return
    if confirmar("¿Separar la cuenta del empleado? Ambos seguirán guardados"):
        informar(EmpleadoDAO.desvincular_cuenta(empleado.id_empleado),
                 "Cuenta desvinculada.", "El empleado ya no existe.")


def eliminar_empleado():
    empleado = seleccionar_empleado()
    if confirmar(f"¿Eliminar a {empleado.nombre}? Debe estar sin horas guardadas y no ser gerente"):
        informar(EmpleadoDAO.eliminar(empleado.id_empleado), "Empleado eliminado.", "El empleado ya no existe.")


def menu_empleado(usuario):
    submenu("Empleados", {
        "1": ("Registrar", registrar_empleado),
        "2": ("Listar", lambda: mostrar_lista("Empleados", EmpleadoDAO.listar())),
        "3": ("Buscar y ver relaciones", buscar_empleado),
        "4": ("Actualizar datos", actualizar_empleado),
        "5": ("Eliminar", eliminar_empleado),
        "6": ("Vincular una cuenta existente", vincular_cuenta),
        "7": ("Desvincular la cuenta", desvincular_cuenta),
    }, usuario, "empleados")
