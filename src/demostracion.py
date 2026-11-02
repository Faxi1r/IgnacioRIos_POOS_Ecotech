"""Prueba un recorrido completo en una base temporal, sin tocar los datos del usuario."""
import os
from datetime import date
from tempfile import TemporaryDirectory
from pathlib import Path

from src.dependencia import Administrador, Departamento, Empleado, Proyecto, Usuario
from src.persistencia import (
    DepartamentoDAO, EmpleadoDAO, InformeDAO, ProyectoDAO, RegistroTiempoDAO, UsuarioDAO, crear_tablas,
)


def _recorrido(carpeta):
    crear_tablas()
    admin = Administrador(None, "admin_prueba")
    admin.establecer_contrasena("Prueba2026*")
    UsuarioDAO.insertar(admin)
    cuenta = Usuario(None, "ana_prueba")
    cuenta.establecer_contrasena("Prueba2026*")
    UsuarioDAO.insertar(cuenta)
    ana = EmpleadoDAO.insertar(Empleado(None, "PRUEBA001", "Ana Pérez", "ana@prueba.example",
                                       900000, "Calle de Prueba 10", "+56 912345678", date(2026, 3, 1)))
    EmpleadoDAO.vincular_cuenta(ana.id_empleado, cuenta.id_usuario)
    departamento = DepartamentoDAO.insertar(Departamento(None, "Tecnología", ana))
    proyecto = ProyectoDAO.insertar(Proyecto(None, "Ahorro de agua", "Revisar sensores", date(2026, 3, 1)))
    ProyectoDAO.asignar_empleado(proyecto.id_proyecto, ana.id_empleado)
    proyecto = ProyectoDAO.buscar_por_id(proyecto.id_proyecto)
    registro = ana.registrar_horas(date(2026, 3, 16), proyecto, 3.5, "Revisión de sensores")
    RegistroTiempoDAO.insertar(registro)
    informe = admin.generar_informe("Prueba completa", EmpleadoDAO.listar(), DepartamentoDAO.listar(),
                                    ProyectoDAO.listar(), RegistroTiempoDAO.listar())
    InformeDAO.insertar(informe)
    informe = InformeDAO.buscar_por_id(informe.id_informe)
    informe.exportar_pdf(str(carpeta / "prueba.pdf"))
    informe.exportar_excel(str(carpeta / "prueba.xlsx"))
    if not UsuarioDAO.autenticar("ana_prueba", "Prueba2026*"):
        raise RuntimeError("Falló el acceso de la cuenta de prueba.")
    if RegistroTiempoDAO.total_horas_proyecto(proyecto.id_proyecto) != 3.5:
        raise RuntimeError("El total de horas no coincide.")
    ProyectoDAO.desasignar_empleado(proyecto.id_proyecto, ana.id_empleado)
    if RegistroTiempoDAO.buscar_por_id(registro.id_registro) is None:
        raise RuntimeError("Se perdió el historial al quitar una asignación.")
    ana.nombre = "Ana Pérez Soto"
    EmpleadoDAO.actualizar(ana)
    if EmpleadoDAO.buscar_por_id(ana.id_empleado).nombre != "Ana Pérez Soto":
        raise RuntimeError("No se actualizó el nombre.")
    RegistroTiempoDAO.eliminar(registro.id_registro)
    ProyectoDAO.eliminar(proyecto.id_proyecto)
    DepartamentoDAO.eliminar(departamento.id_departamento)
    EmpleadoDAO.eliminar(ana.id_empleado)
    InformeDAO.eliminar(informe.id_informe)
    cuenta.desactivar()
    UsuarioDAO.actualizar(cuenta)
    if UsuarioDAO.autenticar("ana_prueba", "Prueba2026*") is not None:
        raise RuntimeError("Una cuenta desactivada pudo iniciar sesión.")


def ejecutar_demostracion():
    anteriores = {nombre: os.environ.get(nombre) for nombre in ("DB_ENGINE", "DB_NAME")}
    try:
        with TemporaryDirectory() as temporal:
            carpeta = Path(temporal)
            os.environ["DB_ENGINE"] = "sqlite"
            os.environ["DB_NAME"] = str(carpeta / "demostracion.db")
            _recorrido(carpeta)
        print("Demostración correcta: cuentas, empleados, departamentos, proyectos, horas, PDF y Excel.")
        print("Se usó una base SQLite temporal. Los datos de su base se conservan.")
    finally:
        for nombre, valor in anteriores.items():
            if valor is None:
                os.environ.pop(nombre, None)
            else:
                os.environ[nombre] = valor
