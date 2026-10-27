from typing import List, Optional

from src.dependencia.informe import Informe
from src.dependencia.seguridad import Seguridad
from src.persistencia.conexion import marcador_sql
from src.persistencia.dao_util import (
    DAOError,
    convertir_fecha,
    exigir_guardado,
    exigir_nuevo,
    fecha_a_texto,
    sesion_bd,
)

_SELECT = "SELECT id_informe, tipo, fecha_generacion, contenido, creado_por FROM informe"


class InformeDAO:
    """Persistencia de Informe. creado_por es el id del Administrador que lo generó (relación 'genera')."""

    @staticmethod
    def _fila_a_informe(fila) -> Informe:
        return Informe(fila[0], fila[1], convertir_fecha(fila[2]), Seguridad().descifrar(fila[3]), fila[4])

    @staticmethod
    def insertar(informe: Informe) -> Informe:
        informe._datos()
        exigir_nuevo(informe.id_informe, "El informe")
        if informe.creado_por is None:
            raise DAOError("Seleccione un administrador guardado para crear el informe.")
        if not informe.contenido.strip():
            raise DAOError("Genere el contenido del informe antes de guardarlo.")
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(f"SELECT u.activo FROM administrador a JOIN usuario u ON u.id_usuario = a.id_usuario "
                           f"WHERE a.id_usuario = {p}", (informe.creado_por,))
            autor = cursor.fetchone()
            if autor is None or not autor[0]:
                raise DAOError("El informe necesita un administrador activo como autor.")
            cursor.execute(
                f"INSERT INTO informe (tipo, fecha_generacion, contenido, creado_por) VALUES ({p}, {p}, {p}, {p})",
                (informe.tipo, fecha_a_texto(informe.fecha_generacion), Seguridad().cifrar(informe.contenido), informe.creado_por),
            )
            nuevo_id = cursor.lastrowid
        informe.id_informe = nuevo_id
        return informe

    @staticmethod
    def buscar_por_id(id_informe: int) -> Optional[Informe]:
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(f"{_SELECT} WHERE id_informe = {p}", (id_informe,))
            fila = cursor.fetchone()
        return InformeDAO._fila_a_informe(fila) if fila else None

    @staticmethod
    def listar() -> List[Informe]:
        with sesion_bd() as cursor:
            cursor.execute(f"{_SELECT} ORDER BY id_informe DESC")
            filas = cursor.fetchall()
        return [InformeDAO._fila_a_informe(fila) for fila in filas]

    @staticmethod
    def actualizar(informe: Informe) -> bool:
        informe._datos()
        exigir_guardado(informe.id_informe, "El informe")
        if not informe.contenido.strip():
            raise DAOError("El informe debe tener contenido antes de actualizarlo.")
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(f"SELECT creado_por FROM informe WHERE id_informe = {p}", (informe.id_informe,))
            fila = cursor.fetchone()
            if fila is None:
                return False
            if fila[0] != informe.creado_por:
                raise DAOError("El autor de un informe guardado no se cambia. Genere otro informe.")
            cursor.execute(
                f"UPDATE informe SET tipo = {p}, fecha_generacion = {p}, contenido = {p}, creado_por = {p} WHERE id_informe = {p}",
                (informe.tipo, fecha_a_texto(informe.fecha_generacion), Seguridad().cifrar(informe.contenido), informe.creado_por, informe.id_informe),
            )
            return cursor.rowcount > 0

    @staticmethod
    def eliminar(id_informe: int) -> bool:
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(f"DELETE FROM informe WHERE id_informe = {p}", (id_informe,))
            return cursor.rowcount > 0
