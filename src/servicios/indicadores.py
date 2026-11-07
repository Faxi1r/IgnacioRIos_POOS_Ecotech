"""Consulta, respaldo local y conversión de indicadores financieros."""
import logging
import re
from decimal import Decimal, ROUND_HALF_UP

from src.indicadores import ErrorAPI, crear_indicadores, obtener_datos, validar_codigo
from src.persistencia import ConexionError, DAOError
from src.persistencia.indicador_dao import IndicadorDAO
from src.servicios.permisos import exigir_sesion

logger = logging.getLogger(__name__)
FUENTE = "open.er-api.com"
UNIDAD = "Pesos"


def consultar_indicador(sesion, codigo):
    """Devuelve (indicador, origen, mensaje); el indicador puede ser None."""
    exigir_sesion(sesion)
    codigo = validar_codigo(codigo)
    try:
        indicadores = crear_indicadores(obtener_datos(codigo), codigo)
    except (ErrorAPI, ValueError, TypeError) as error:
        logger.warning("Consulta de %s fallida: %s", codigo, type(error).__name__)
        historial = IndicadorDAO.listar_historial(codigo, 1, FUENTE, UNIDAD)
        if not historial:
            return None, "BD", f"{error} No hay un respaldo compatible guardado."
        return historial[0], "BD", f"{error} Se muestra el último dato guardado; no es una consulta nueva."

    indicador = max(indicadores, key=lambda item: item.fecha)
    try:
        IndicadorDAO.guardar_varios(indicadores)
    except (DAOError, ConexionError) as error:
        logger.warning("No se pudo guardar el indicador: %s", type(error).__name__)
        return indicador, "API", "La consulta fue correcta, pero no se pudo guardar en el historial."
    return indicador, "API", "El dato quedó guardado en el historial local."


def consultar_historial(sesion, codigo, limite=20):
    exigir_sesion(sesion)
    codigo = validar_codigo(codigo)
    return IndicadorDAO.listar_historial(codigo, limite, FUENTE, UNIDAD)


def validar_monto(texto):
    """CLP sin separadores de miles, entre cero y mil millones, hasta dos decimales."""
    if not isinstance(texto, str):
        raise ValueError("Ingrese un monto numérico.")
    texto = texto.strip().replace(",", ".")
    if len(texto) > 20 or not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", texto):
        raise ValueError("Use un monto sin separadores de miles y con hasta dos decimales.")
    monto = Decimal(texto)
    if not 0 <= monto <= Decimal("1000000000"):
        raise ValueError("El monto debe estar entre 0 y 1.000.000.000 CLP.")
    return monto


def convertir_monto(sesion, texto, indicador):
    exigir_sesion(sesion)
    monto = validar_monto(texto)
    resultado = monto / Decimal(str(indicador.valor))
    if not resultado.is_finite() or resultado > Decimal("1000000000000000"):
        raise ValueError("El resultado supera el límite de conversión permitido.")
    return resultado.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
