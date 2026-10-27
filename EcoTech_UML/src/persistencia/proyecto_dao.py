from typing import List, Optional

from src.dependencia.proyecto import Proyecto
from src.persistencia.conexion import marcador_sql
from src.persistencia.dao_util import (
    DAOError,
    convertir_fecha,
    exigir_guardado,
    exigir_nuevo,
    fecha_a_texto,
    sesion_bd,
)
from src.persistencia.empleado_dao import EmpleadoDAO

_SELECT = "SELECT id_proyecto, nombre, descripcion, fecha_inicio FROM proyecto"


class ProyectoDAO:
    """Persistencia de Proyecto. La relación 'asignado a' (0..* a 0..*) usa la tabla proyecto_empleado."""

    @staticmethod
    def _fila_a_proyecto(fila) -> Proyecto:
        """Reconstruye el Proyecto y carga sus empleados asignados."""
        proyecto = Proyecto(fila[0], fila[1], fila[2], convertir_fecha(fila[3]))
        for empleado in EmpleadoDAO.listar_por_proyecto(proyecto.id_proyecto):
            proyecto.asignar_empleado(empleado)
        from src.persistencia.registro_tiempo_dao import RegistroTiempoDAO
        proyecto._registros_tiempo = RegistroTiempoDAO.listar_por_proyecto(proyecto.id_proyecto)
        return proyecto

    @staticmethod
    def buscar_por_nombre(nombre: str) -> Optional[Proyecto]:
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(f"{_SELECT} WHERE nombre = {p}", (nombre.strip(),))
            fila = cursor.fetchone()
        return ProyectoDAO._fila_a_proyecto(fila) if fila else None

    @staticmethod
    def insertar(proyecto: Proyecto) -> Proyecto:
        proyecto.validar_datos()
        exigir_nuevo(proyecto.id_proyecto, "El proyecto")
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(
                f"INSERT INTO proyecto (nombre, descripcion, fecha_inicio) VALUES ({p}, {p}, {p})",
                (proyecto.nombre, proyecto.descripcion, fecha_a_texto(proyecto.fecha_inicio)),
            )
            nuevo_id = cursor.lastrowid
            for empleado in proyecto.empleados_asignados:
                exigir_guardado(empleado.id_empleado, "El empleado asignado")
                cursor.execute(f"INSERT INTO proyecto_empleado (id_proyecto, id_empleado) VALUES ({p}, {p})",
                               (nuevo_id, empleado.id_empleado))
        proyecto.id_proyecto = nuevo_id
        return proyecto

    @staticmethod
    def buscar_por_id(id_proyecto: int) -> Optional[Proyecto]:
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(f"{_SELECT} WHERE id_proyecto = {p}", (id_proyecto,))
            fila = cursor.fetchone()
        return ProyectoDAO._fila_a_proyecto(fila) if fila else None

    @staticmethod
    def listar() -> List[Proyecto]:
        with sesion_bd() as cursor:
            cursor.execute(f"{_SELECT} ORDER BY id_proyecto")
            filas = cursor.fetchall()
        return [ProyectoDAO._fila_a_proyecto(fila) for fila in filas]

    @staticmethod
    def actualizar(proyecto: Proyecto) -> bool:
        proyecto.validar_datos()
        exigir_guardado(proyecto.id_proyecto, "El proyecto")
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(
                f"UPDATE proyecto SET nombre = {p}, descripcion = {p}, fecha_inicio = {p} WHERE id_proyecto = {p}",
                (proyecto.nombre, proyecto.descripcion, fecha_a_texto(proyecto.fecha_inicio), proyecto.id_proyecto),
            )
            return cursor.rowcount > 0

    @staticmethod
    def eliminar(id_proyecto: int) -> bool:
        """Solo se elimina si no tiene horas guardadas."""
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(f"SELECT 1 FROM registro_tiempo WHERE id_proyecto = {p}", (id_proyecto,))
            if cursor.fetchone() is not None:
                raise DAOError("El proyecto tiene horas guardadas. No se elimina para conservar ese historial.")
            cursor.execute(f"DELETE FROM proyecto WHERE id_proyecto = {p}", (id_proyecto,))
            return cursor.rowcount > 0

    @staticmethod
    def asignar_empleado(id_proyecto: int, id_empleado: int) -> bool:
        """
        Persistencia de asignar_empleado(). True si se asignó; False si ya estaba asignado.
        Si el proyecto o el empleado no existen, la BD lo rechaza (DAOIntegridadError).
        """
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(
                f"SELECT 1 FROM proyecto_empleado WHERE id_proyecto = {p} AND id_empleado = {p}",
                (id_proyecto, id_empleado),
            )
            if cursor.fetchone() is not None:
                return False
            cursor.execute(
                f"INSERT INTO proyecto_empleado (id_proyecto, id_empleado) VALUES ({p}, {p})",
                (id_proyecto, id_empleado),
            )
            return True

    @staticmethod
    def desasignar_empleado(id_proyecto: int, id_empleado: int) -> bool:
        """Persistencia de desasignar_empleado(): True si la asignación existía."""
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(
                f"DELETE FROM proyecto_empleado WHERE id_proyecto = {p} AND id_empleado = {p}",
                (id_proyecto, id_empleado),
            )
            return cursor.rowcount > 0
