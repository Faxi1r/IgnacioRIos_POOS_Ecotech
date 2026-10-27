"""Opciones de una cuenta común: sus propios datos y sus horas."""
from src.persistencia import EmpleadoDAO, ProyectoDAO, RegistroTiempoDAO, UsuarioDAO
from .comunes import mostrar_lista, pedir_contrasena, submenu
from .menu_registro import registrar_para_empleado


def buscar_mi_empleado(usuario):
    empleado = EmpleadoDAO.buscar_por_usuario(usuario.id_usuario)
    if empleado is None:
        print("Su cuenta todavía no está vinculada a un empleado. Puede pedirlo al administrador.")
    return empleado


def ver_mis_datos(usuario):
    empleado = buscar_mi_empleado(usuario)
    if empleado:
        print(empleado)
        print(f"Correo: {empleado.correo}")
        print(f"Departamento: {empleado.departamento.nombre if empleado.departamento else 'Sin departamento'}")


def ver_mis_proyectos(usuario):
    empleado = buscar_mi_empleado(usuario)
    if empleado:
        proyectos = [p for p in ProyectoDAO.listar() if empleado in p.empleados_asignados]
        mostrar_lista("Mis proyectos", proyectos)


def ver_mis_horas(usuario):
    empleado = buscar_mi_empleado(usuario)
    if empleado:
        mostrar_lista("Mis horas", RegistroTiempoDAO.listar_por_empleado(empleado.id_empleado))


def registrar_mis_horas(usuario):
    empleado = buscar_mi_empleado(usuario)
    if empleado:
        registrar_para_empleado(empleado)


def cambiar_mi_contrasena(usuario):
    actual = UsuarioDAO.buscar_por_id(usuario.id_usuario)
    if actual is None:
        print("La cuenta ya no existe.")
        return
    actual.establecer_contrasena(pedir_contrasena())
    UsuarioDAO.actualizar(actual)
    print("Contraseña actualizada.")


def menu_personal(usuario):
    submenu(f"Mi cuenta: {usuario.nombre_usuario}", {
        "1": ("Ver mis datos", lambda: ver_mis_datos(usuario)),
        "2": ("Ver mis proyectos", lambda: ver_mis_proyectos(usuario)),
        "3": ("Ver mis horas", lambda: ver_mis_horas(usuario)),
        "4": ("Registrar mis horas", lambda: registrar_mis_horas(usuario)),
        "5": ("Cambiar mi contraseña", lambda: cambiar_mi_contrasena(usuario)),
    }, usuario, "mi_cuenta")
