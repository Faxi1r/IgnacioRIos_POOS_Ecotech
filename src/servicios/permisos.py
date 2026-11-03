from src.persistencia import EmpleadoDAO, UsuarioDAO


def exigir_sesion(sesion):
    if not isinstance(sesion, dict):
        raise PermissionError("Inicie sesión.")
    if sesion.get("rol") not in ("admin", "empleado"):
        raise PermissionError("Acceso no permitido.")
    empleado_id = sesion.get("empleado_id")
    if type(empleado_id) is not int or empleado_id <= 0:
        raise PermissionError("Sesión inválida.")
    if type(sesion.get("id")) is not int or sesion["id"] <= 0:
        raise PermissionError("Sesión inválida.")

    # También revisamos si desactivaron o desvincularon la cuenta mientras estaba abierta.
    cuenta = UsuarioDAO.buscar_por_id(sesion["id"])
    empleado = EmpleadoDAO.buscar_por_usuario(sesion["id"])
    if (
        cuenta is None
        or not cuenta.activo
        or cuenta.rol != sesion["rol"]
        or empleado is None
        or empleado.id_empleado != empleado_id
    ):
        raise PermissionError("La sesión ya no es válida. Inicie sesión nuevamente.")


def exigir_admin(sesion):
    exigir_sesion(sesion)
    if sesion["rol"] != "admin":
        raise PermissionError("Acción solo para administrador.")
