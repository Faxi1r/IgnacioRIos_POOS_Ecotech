from typing import List, Optional

from src.dependencia.registro_tiempo import RegistroDeTiempo
from src.dependencia.seguridad import Seguridad
from src.persistencia.conexion import marcador_sql
from src.persistencia.dao_util import (
    DAOError,
    DAOIntegridadError,
    convertir_fecha,
    exigir_guardado,
    exigir_nuevo,
    fecha_a_texto,
    sesion_bd,
)

_SELECT = (
    "SELECT id_registro, fecha, horas, descripcion_tareas, id_empleado, id_proyecto FROM registro_tiempo"
)


class RegistroTiempoDAO:
    """Guarda las horas de un empleado en un proyecto."""

    @staticmethod
    def _validar_registro(cursor, registro, revisar_asignacion=True):
        registro.validar_datos()
        p = marcador_sql()
        if registro.id_empleado is None or registro.id_proyecto is None:
            raise DAOError("Guarde primero al empleado y al proyecto antes de registrar horas.")
        cursor.execute(f"SELECT 1 FROM empleado WHERE id_empleado = {p}", (registro.id_empleado,))
        if cursor.fetchone() is None:
            raise DAOIntegridadError("No encontramos al empleado del registro de horas.")
        cursor.execute(f"SELECT 1 FROM proyecto WHERE id_proyecto = {p}", (registro.id_proyecto,))
        if cursor.fetchone() is None:
            raise DAOIntegridadError("No encontramos el proyecto del registro de horas.")
        if revisar_asignacion:
            cursor.execute(f"SELECT 1 FROM proyecto_empleado WHERE id_empleado = {p} AND id_proyecto = {p}",
                           (registro.id_empleado, registro.id_proyecto))
            if cursor.fetchone() is None:
                raise DAOError("Asigne primero al empleado al proyecto antes de registrar sus horas.")
        # Se suman todas las horas del día, aunque sean de proyectos distintos.
        cursor.execute(
            f"SELECT COALESCE(SUM(horas), 0) FROM registro_tiempo "
            f"WHERE id_empleado = {p} AND fecha = {p} AND id_registro <> {p}",
            (registro.id_empleado, fecha_a_texto(registro.fecha), registro.id_registro or -1),
        )
        if float(cursor.fetchone()[0]) + registro.horas > 24 + 1e-9:
            raise DAOError("El empleado no puede acumular más de 24 horas en una misma fecha.")

    @staticmethod
    def _fila_a_registro(fila) -> RegistroDeTiempo:
        return RegistroDeTiempo(
            id_registro=fila[0],
            fecha=convertir_fecha(fila[1]),
            horas=float(fila[2]),  # MySQL entrega Decimal
            descripcion_tareas=Seguridad().descifrar(fila[3]),
            id_empleado=fila[4],
            id_proyecto=fila[5],
        )

    @staticmethod
    def insertar(registro: RegistroDeTiempo) -> RegistroDeTiempo:
        exigir_nuevo(registro.id_registro, "El registro de tiempo")
        p = marcador_sql()
        with sesion_bd() as cursor:
            RegistroTiempoDAO._validar_registro(cursor, registro)
            cursor.execute(
                f"INSERT INTO registro_tiempo (id_empleado, id_proyecto, fecha, horas, descripcion_tareas) "
                f"VALUES ({p}, {p}, {p}, {p}, {p})",
                (
                    registro.id_empleado,
                    registro.id_proyecto,
                    fecha_a_texto(registro.fecha),
                    registro.horas,
                    Seguridad().cifrar(registro.descripcion_tareas),
                ),
            )
            nuevo_id = cursor.lastrowid
        registro.id_registro = nuevo_id
        return registro

    @staticmethod
    def buscar_por_id(id_registro: int) -> Optional[RegistroDeTiempo]:
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(f"{_SELECT} WHERE id_registro = {p}", (id_registro,))
            fila = cursor.fetchone()
        return RegistroTiempoDAO._fila_a_registro(fila) if fila else None

    @staticmethod
    def listar() -> List[RegistroDeTiempo]:
        with sesion_bd() as cursor:
            cursor.execute(f"{_SELECT} ORDER BY fecha DESC, id_registro DESC")
            filas = cursor.fetchall()
        return [RegistroTiempoDAO._fila_a_registro(fila) for fila in filas]

    @staticmethod
    def listar_por_empleado(id_empleado: int) -> List[RegistroDeTiempo]:
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(
                f"{_SELECT} WHERE id_empleado = {p} ORDER BY fecha DESC, id_registro DESC", (id_empleado,)
            )
            filas = cursor.fetchall()
        return [RegistroTiempoDAO._fila_a_registro(fila) for fila in filas]

    @staticmethod
    def listar_por_proyecto(id_proyecto: int) -> List[RegistroDeTiempo]:
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(
                f"{_SELECT} WHERE id_proyecto = {p} ORDER BY fecha DESC, id_registro DESC", (id_proyecto,)
            )
            filas = cursor.fetchall()
        return [RegistroTiempoDAO._fila_a_registro(fila) for fila in filas]

    @staticmethod
    def total_horas_proyecto(id_proyecto: int) -> float:
        """Suma las horas guardadas para ese proyecto."""
        return round(sum(r.horas for r in RegistroTiempoDAO.listar_por_proyecto(id_proyecto)), 2)

    @staticmethod
    def actualizar(registro: RegistroDeTiempo) -> bool:
        """Modifica fecha, horas y descripción (el empleado y el proyecto no cambian)."""
        exigir_guardado(registro.id_registro, "El registro de tiempo")
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(f"SELECT id_empleado, id_proyecto FROM registro_tiempo WHERE id_registro = {p}",
                           (registro.id_registro,))
            anterior = cursor.fetchone()
            if anterior is None:
                return False
            if tuple(anterior) != (registro.id_empleado, registro.id_proyecto):
                raise DAOError("No se puede cambiar el empleado ni el proyecto de un registro ya guardado.")
            RegistroTiempoDAO._validar_registro(cursor, registro, revisar_asignacion=False)
            cursor.execute(
                f"UPDATE registro_tiempo SET fecha = {p}, horas = {p}, descripcion_tareas = {p} "
                f"WHERE id_registro = {p}",
                (fecha_a_texto(registro.fecha), registro.horas, Seguridad().cifrar(registro.descripcion_tareas), registro.id_registro),
            )
            return cursor.rowcount > 0

    @staticmethod
    def eliminar(id_registro: int) -> bool:
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(f"DELETE FROM registro_tiempo WHERE id_registro = {p}", (id_registro,))
            return cursor.rowcount > 0
