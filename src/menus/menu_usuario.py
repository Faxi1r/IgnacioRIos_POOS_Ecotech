from src.servicios import gestion_empleados, gestion_usuarios
from src.servicios.permisos import exigir_admin
from .comunes import (
    confirmar,
    informar,
    mostrar_lista,
    pedir_contrasena,
    pedir_nombre_usuario_nuevo,
    pedir_objeto,
    submenu,
)


def crear_usuario(sesion):
    exigir_admin(sesion)
    empleado = pedir_objeto(
        "Id del empleado sin cuenta: ",
        lambda identificador: gestion_empleados.buscar_por_id(sesion, identificador),
        "un empleado",
    )
    if empleado.usuario is not None:
        print("El empleado ya tiene cuenta.")
        return
    usuario = gestion_usuarios.registrar_cuenta(
        sesion, empleado.id_empleado, pedir_nombre_usuario_nuevo(), pedir_contrasena()
    )
    print(f"Cuenta de empleado guardada. Id: {usuario.id_usuario}.")
    return usuario


def seleccionar_usuario(sesion):
    exigir_admin(sesion)
    return pedir_objeto(
        "Id del usuario: ",
        lambda identificador: gestion_usuarios.buscar_por_id(sesion, identificador),
        "un usuario",
    )


def actualizar_usuario(sesion):
    exigir_admin(sesion)
    usuario = seleccionar_usuario(sesion)
    print(usuario)
    if confirmar("¿Cambiar el nombre de usuario?"):
        usuario.nombre_usuario = pedir_nombre_usuario_nuevo(usuario.id_usuario)
    if confirmar("¿Cambiar la contraseña?"):
        usuario.establecer_contrasena(pedir_contrasena())
    informar(
        gestion_usuarios.actualizar(sesion, usuario),
        "Cuenta actualizada.",
        "La cuenta ya no existe.",
    )


def desactivar_usuario(sesion):
    exigir_admin(sesion)
    usuario = seleccionar_usuario(sesion)
    if usuario.id_usuario == sesion["id"]:
        print("No puede desactivar la cuenta con la que está trabajando.")
        return
    if confirmar(f"¿Desactivar la cuenta {usuario.nombre_usuario}? Se conservarán sus informes"):
        informar(
            gestion_usuarios.desactivar(sesion, usuario.id_usuario),
            "Cuenta desactivada.",
            "La cuenta ya no existe.",
        )


def menu_usuario(sesion):
    submenu(
        "Cuentas de usuario",
        {
            "1": ("Crear cuenta de empleado", lambda: crear_usuario(sesion)),
            "2": (
                "Listar cuentas",
                lambda: mostrar_lista("Cuentas", gestion_usuarios.listar(sesion)),
            ),
            "3": ("Buscar cuenta", lambda: print(seleccionar_usuario(sesion))),
            "4": ("Actualizar nombre o contraseña", lambda: actualizar_usuario(sesion)),
            "5": ("Desactivar cuenta", lambda: desactivar_usuario(sesion)),
        },
        sesion,
        "usuarios",
    )
