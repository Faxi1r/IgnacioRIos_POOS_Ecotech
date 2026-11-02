"""Datos ficticios para practicar. Repetir la carga no los duplica."""
from datetime import date

from src.dependencia import Administrador, Departamento, Empleado, Proyecto, RegistroDeTiempo, Usuario
from src.persistencia import (
    DepartamentoDAO, EmpleadoDAO, InformeDAO, ProyectoDAO, RegistroTiempoDAO, UsuarioDAO, crear_tablas,
)

CLAVE_DEMO = "Demo2026*"  # Solo para las cuentas de práctica.


def cargar_semilla():
    crear_tablas()
    admin = UsuarioDAO.buscar_por_nombre("admin_demo")
    if admin is None:
        admin = Administrador(None, "admin_demo")
        admin.establecer_contrasena(CLAVE_DEMO)
        UsuarioDAO.insertar(admin)
    if not isinstance(admin, Administrador) or not admin.activo:
        raise ValueError("admin_demo debe ser una cuenta de administrador activa.")

    cuenta_ana = UsuarioDAO.buscar_por_nombre("ana_demo")
    if cuenta_ana is None:
        cuenta_ana = Usuario(None, "ana_demo")
        cuenta_ana.establecer_contrasena(CLAVE_DEMO)
        UsuarioDAO.insertar(cuenta_ana)

    empleados = []
    for identificacion, nombre, correo, telefono in [
        ("DEMO0001", "Ana Torres", "ana@ecotech.example", "+56 9 1234 5678"),
        ("DEMO0002", "Luis Gómez", "luis@ecotech.example", "+56 9 8765 4321"),
    ]:
        empleado = EmpleadoDAO.buscar_por_identificacion(identificacion)
        if empleado is None:
            empleado = Empleado(None, identificacion, nombre, correo, 1000000,
                                "Calle de Ejemplo 123", telefono, date(2026, 3, 1))
            EmpleadoDAO.insertar(empleado)
        empleados.append(empleado)
    # Ana tiene cuenta; Luis puede trabajar sin necesitar acceso al programa.
    if empleados[0].usuario is None and cuenta_ana.activo:
        EmpleadoDAO.vincular_cuenta(empleados[0].id_empleado, cuenta_ana.id_usuario)

    departamento = DepartamentoDAO.buscar_por_nombre("[DEMO] Tecnología")
    if departamento is None:
        departamento = Departamento(None, "[DEMO] Tecnología", empleados[0], empleados)
        DepartamentoDAO.insertar(departamento)

    proyecto = ProyectoDAO.buscar_por_nombre("[DEMO] Ahorro de energía")
    if proyecto is None:
        proyecto = ProyectoDAO.insertar(Proyecto(None, "[DEMO] Ahorro de energía",
                                                "Medir el consumo de la oficina", date(2026, 3, 1)))
    for empleado, horas, tarea in zip(empleados, [4, 2.5], ["Semilla: desarrollo", "Semilla: pruebas"]):
        ProyectoDAO.asignar_empleado(proyecto.id_proyecto, empleado.id_empleado)
        registros = RegistroTiempoDAO.listar_por_empleado(empleado.id_empleado)
        existe = any(r.id_proyecto == proyecto.id_proyecto and r.fecha == date(2026, 3, 16)
                     and r.descripcion_tareas == tarea for r in registros)
        if not existe:
            RegistroTiempoDAO.insertar(RegistroDeTiempo(None, date(2026, 3, 16), horas, tarea,
                                                       empleado.id_empleado, proyecto.id_proyecto))

    if not any(i.tipo == "Resumen Demo" and i.creado_por == admin.id_usuario for i in InformeDAO.listar()):
        InformeDAO.insertar(admin.generar_informe(
            "Resumen Demo", EmpleadoDAO.listar(), DepartamentoDAO.listar(),
            ProyectoDAO.listar(), RegistroTiempoDAO.listar()))

    cantidades = {
        "usuarios": len(UsuarioDAO.listar()), "empleados": len(EmpleadoDAO.listar()),
        "departamentos": len(DepartamentoDAO.listar()), "proyectos": len(ProyectoDAO.listar()),
        "registros": len(RegistroTiempoDAO.listar()), "informes": len(InformeDAO.listar()),
    }
    print(f"Semilla revisada. Cantidades actuales: {cantidades}")
    print("Cuentas de práctica: admin_demo y ana_demo. Clave inicial: Demo2026*.")
    print("Si ya cambió sus contraseñas, se mantienen las que usted eligió.")
    return cantidades


if __name__ == "__main__":
    cargar_semilla()
