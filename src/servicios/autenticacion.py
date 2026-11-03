from src.persistencia import EmpleadoDAO, UsuarioDAO


def autenticar(nombre_usuario, contrasena):
    cuenta = UsuarioDAO.autenticar(nombre_usuario, contrasena)
    if cuenta is None:
        return None
    empleado = EmpleadoDAO.buscar_por_usuario(cuenta.id_usuario)
    if empleado is None:
        raise PermissionError(
            "La cuenta no tiene un empleado vinculado. Contacte al administrador."
        )
    return {
        "id": cuenta.id_usuario,
        "empleado_id": empleado.id_empleado,
        "nombre_usuario": cuenta.nombre_usuario,
        "rol": cuenta.rol,
    }


def cerrar_sesion(sesion):
    if isinstance(sesion, dict):
        sesion.clear()
