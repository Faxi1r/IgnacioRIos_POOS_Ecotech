from src.dependencia import Administrador, Usuario
from src.persistencia import UsuarioDAO
from .comunes import (
    confirmar, informar, mostrar_lista, pedir_contrasena,
    pedir_nombre_usuario_nuevo, pedir_objeto, submenu,
)


def crear_usuario(es_admin=False):
    clase = Administrador if es_admin else Usuario
    usuario = clase(None, pedir_nombre_usuario_nuevo())
    usuario.establecer_contrasena(pedir_contrasena())
    UsuarioDAO.insertar(usuario)
    print(f"Cuenta guardada correctamente. Id: {usuario.id_usuario}.")
    return usuario


def seleccionar_usuario():
    return pedir_objeto("Id del usuario: ", UsuarioDAO.buscar_por_id, "un usuario")


def actualizar_usuario():
    usuario = seleccionar_usuario()
    print(usuario)
    if confirmar("¿Cambiar el nombre de usuario?"):
        usuario.nombre_usuario = pedir_nombre_usuario_nuevo(usuario.id_usuario)
    if confirmar("¿Cambiar la contraseña?"):
        usuario.establecer_contrasena(pedir_contrasena())
    informar(UsuarioDAO.actualizar(usuario), "Cuenta actualizada.", "La cuenta ya no existe.")


def desactivar_usuario(usuario_actual):
    usuario = seleccionar_usuario()
    if usuario.id_usuario == usuario_actual.id_usuario:
        print("No puede desactivar la cuenta con la que está trabajando.")
        return
    if confirmar(f"¿Desactivar la cuenta {usuario.nombre_usuario}? Se conservarán sus informes"):
        usuario.desactivar()
        informar(UsuarioDAO.actualizar(usuario), "Cuenta desactivada.", "La cuenta ya no existe.")


def menu_usuario(usuario_actual):
    submenu("Usuarios y administradores", {
        "1": ("Crear usuario", crear_usuario),
        "2": ("Crear administrador", lambda: crear_usuario(es_admin=True)),
        "3": ("Listar cuentas", lambda: mostrar_lista("Cuentas", UsuarioDAO.listar())),
        "4": ("Buscar cuenta", lambda: print(seleccionar_usuario())),
        "5": ("Actualizar cuenta", actualizar_usuario),
        "6": ("Desactivar cuenta", lambda: desactivar_usuario(usuario_actual)),
    }, usuario_actual, "usuarios")
