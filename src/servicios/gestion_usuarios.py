from src.dependencia import Usuario
from src.persistencia import UsuarioDAO
from .permisos import exigir_admin


def registrar_cuenta(sesion, id_empleado, nombre_usuario, contrasena):
    exigir_admin(sesion)
    # La cuenta habitual siempre es empleado; el formulario no recibe un rol.
    usuario = Usuario(None, nombre_usuario, rol="empleado")
    usuario.establecer_contrasena(contrasena)
    return UsuarioDAO.insertar_vinculado(usuario, id_empleado)


def listar(sesion):
    exigir_admin(sesion)
    return UsuarioDAO.listar()


def buscar_por_id(sesion, id_usuario):
    exigir_admin(sesion)
    return UsuarioDAO.buscar_por_id(id_usuario)


def actualizar(sesion, usuario):
    exigir_admin(sesion)
    if usuario.id_usuario == sesion["id"] and not usuario.activo:
        raise PermissionError("No puede desactivar su propia sesión.")
    return UsuarioDAO.actualizar(usuario)


def desactivar(sesion, id_usuario):
    exigir_admin(sesion)
    if id_usuario == sesion["id"]:
        raise PermissionError("No puede desactivar su propia sesión.")
    usuario = UsuarioDAO.buscar_por_id(id_usuario)
    if usuario is None:
        raise ValueError("La cuenta no existe.")
    usuario.desactivar()
    return UsuarioDAO.actualizar(usuario)
