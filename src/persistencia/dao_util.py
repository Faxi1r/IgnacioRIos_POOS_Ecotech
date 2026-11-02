"""Ayudas para no repetir la apertura, confirmación y cierre en cada DAO."""
import logging
from contextlib import contextmanager
from datetime import date, datetime
from typing import Iterator, Optional, Union

from src.persistencia.conexion import ERRORES_BD, ERRORES_INTEGRIDAD, abrir_conexion

logger = logging.getLogger(__name__)


class DAOError(Exception):
    """Falla en la capa de persistencia. El mensaje es seguro para mostrar al usuario."""


class DAOIntegridadError(DAOError):
    """Una restricción de la BD rechazó la operación (dato duplicado o referencia inexistente)."""


@contextmanager
def sesion_bd() -> Iterator:
    """
    Entrega un cursor dentro de una transacción:
      - éxito  -> COMMIT
      - fallo  -> ROLLBACK y error propio con mensaje seguro (el detalle técnico va al log)
      - siempre -> se cierran cursor y conexión
    """
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        try:
            yield cursor
            conexion.commit()
        finally:
            cursor.close()
    except ERRORES_INTEGRIDAD as err:
        _revertir(conexion)
        logger.error("Violación de integridad: %s", err)
        detalle = str(err).upper()
        codigo = err.args[0] if err.args else None
        if "UNIQUE" in detalle or codigo == 1062:
            mensaje = "La identificación, el correo, el nombre o la cuenta ya están en uso, o la asignación está repetida. Revise el dato."
        elif "FOREIGN KEY" in detalle or codigo in (1451, 1452):
            mensaje = "La relación no es válida. Compruebe que el empleado, proyecto, departamento o administrador exista."
        else:
            mensaje = "La base rechazó un dato obligatorio o fuera del rango permitido. Revise los datos ingresados."
        raise DAOIntegridadError(mensaje) from err
    except ERRORES_BD as err:
        _revertir(conexion)
        logger.error("Error de base de datos: %s", err)
        raise DAOError("No fue posible completar la operación en la base de datos.") from err
    except Exception:
        _revertir(conexion)
        raise
    finally:
        if conexion is not None:
            conexion.close()


def _revertir(conexion) -> None:
    if conexion is None:
        return
    try:
        conexion.rollback()
    except ERRORES_BD:  # la conexión pudo haberse caído; no ocultamos el error original
        logger.warning("No se pudo hacer rollback")


def exigir_nuevo(identificador: Optional[int], entidad: str) -> None:
    """Un objeto que ya tiene id está guardado: debe usarse actualizar(), no insertar()."""
    if identificador is not None:
        raise DAOError(f"{entidad} ya está guardado (id {identificador}); use actualizar().")


def exigir_guardado(identificador: Optional[int], entidad: str) -> None:
    """Para actualizar hace falta que el objeto ya tenga id."""
    if identificador is None:
        raise DAOError(f"{entidad} aún no está guardado; use insertar() primero.")


def fecha_a_texto(valor: Optional[date]) -> Optional[str]:
    """date -> 'AAAA-MM-DD' (válido para TEXT en SQLite y DATE en MySQL)."""
    return valor.isoformat() if valor is not None else None


def convertir_fecha(valor: Union[date, datetime, str, None]) -> Optional[date]:
    """
    Normaliza lo que devuelve la BD a date: SQLite entrega texto, MySQL entrega date.
    (datetime se revisa primero porque datetime es subclase de date.)
    """
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(str(valor).split(" ")[0])
    except ValueError as err:
        logger.error("Fecha inválida en la base de datos: %r", valor)
        raise DAOError("Se encontró una fecha inválida en la base de datos.") from err
