from src.dependencia import Empleado
from src.persistencia import EmpleadoDAO, ProyectoDAO, RegistroTiempoDAO, UsuarioDAO
from .permisos import exigir_sesion


def mi_ficha(sesion):
    exigir_sesion(sesion)
    empleado = EmpleadoDAO.buscar_por_id(sesion["empleado_id"])
    if empleado is None:
        raise ValueError("Empleado no encontrado.")
    return empleado


def mis_registros(sesion):
    exigir_sesion(sesion)
    return RegistroTiempoDAO.listar_por_empleado(sesion["empleado_id"])


def actualizar_mis_datos(sesion, nombre, correo):
    exigir_sesion(sesion)
    nombre = Empleado.validar_nombre(nombre)
    correo = Empleado.validar_correo(correo)
    empleado = EmpleadoDAO.buscar_por_id(sesion["empleado_id"])
    if empleado is None:
        raise ValueError("Empleado no encontrado.")
    # El ID viene de la sesión. Aquí solo se cambian nombre y correo.
    empleado.nombre, empleado.correo = nombre, correo
    return EmpleadoDAO.actualizar(empleado)


def mis_proyectos(sesion):
    empleado = mi_ficha(sesion)
    return [p for p in ProyectoDAO.listar() if empleado in p.empleados_asignados]


def registrar_mis_horas(sesion, id_proyecto, fecha, horas, tareas):
    empleado = mi_ficha(sesion)
    proyecto = ProyectoDAO.buscar_por_id(id_proyecto)
    if proyecto is None or empleado not in proyecto.empleados_asignados:
        raise PermissionError("Solo puede registrar horas en sus proyectos asignados.")
    registro = empleado.registrar_horas(fecha, proyecto, horas, tareas)
    return RegistroTiempoDAO.insertar(registro)


def cambiar_contrasena(sesion, contrasena):
    exigir_sesion(sesion)
    cuenta = UsuarioDAO.buscar_por_id(sesion["id"])
    cuenta.establecer_contrasena(contrasena)
    return UsuarioDAO.actualizar(cuenta)
