"""Consulta y valida indicadores financieros (changeRate-API)"""
import logging
import math
from datetime import datetime, timezone

import requests

from src.dependencia.indicador import Indicador

logger = logging.getLogger(__name__)

URL_BASE = "https://open.er-api.com/v6/latest"
INDICADORES = {
    "dolar": "Dólar",
    "euro": "Euro",
}
# Moneda que se consulta para cada indicador (la API entrega cuántos CLP vale cada una).
MONEDAS = {"dolar": "USD", "euro": "EUR"}
URL_DOLAR = f"{URL_BASE}/USD"  # Referencia del dólar.
TIMEOUT_API = (3, 5)
FUENTE = "open.er-api.com"


class ErrorAPI(Exception):
    """Error de consulta con un mensaje seguro en pantalla."""


def validar_codigo(codigo):
    """Acepta únicamente indicadores definidos por el sistema."""
    if not isinstance(codigo, str) or codigo not in INDICADORES:
        raise ValueError("Seleccione un indicador válido: dólar o euro.")
    return codigo


def obtener_datos(codigo="dolar"):
    """Solicita los datos al servicio de afuera y controla los errores de laconexión."""
    codigo = validar_codigo(codigo)
    url = f"{URL_BASE}/{MONEDAS[codigo]}"

    respuesta = None
    try:
        respuesta = requests.get(url, timeout=TIMEOUT_API)
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.exceptions.Timeout as error:
        logger.warning("Tiempo de espera agotado al consultar %s", codigo)
        raise ErrorAPI("La API tardó demasiado en responder. Intente nuevamente.") from error
    except requests.exceptions.ConnectionError as error:
        logger.warning("No fue posible conectar con la API")
        raise ErrorAPI("No hay conexión con el servicio de indicadores.") from error
    except requests.exceptions.HTTPError as error:
        estado = getattr(respuesta, "status_code", 0)
        if type(estado) is not int:
            estado = 0
        logger.warning("El servicio respondió con HTTP %s para %s", estado, codigo)
        mensajes = {
            400: "La API rechazó la solicitud. Revise el indicador seleccionado.",
            401: "La API no autorizó la consulta.",
            403: "La API rechazó el acceso a este recurso.",
            404: "No se encontró el indicador solicitado.",
            429: "Se realizaron demasiadas consultas. Intente más tarde.",
        }
        if estado in mensajes:
            mensaje = mensajes[estado]
        elif estado >= 500:
            mensaje = "El servicio de indicadores presenta problemas. Intente más tarde."
        else:
            mensaje = "La API respondió con un error HTTP. Intente más tarde."
        raise ErrorAPI(mensaje) from error
    except requests.exceptions.JSONDecodeError as error:
        logger.warning("La API entregó una respuesta que no es JSON válido")
        raise ErrorAPI("El servicio entregó una respuesta que no se pudo leer.") from error
    except requests.exceptions.RequestException as error:
        logger.warning("Error de comunicación con la API: %s", error)
        raise ErrorAPI("No fue posible comunicarse con el servicio de indicadores.") from error
    except ValueError as error:
        logger.warning("La API entregó una respuesta que no se pudo interpretar")
        raise ErrorAPI("El servicio entregó una respuesta que no se pudo leer.") from error

    finally:
        if respuesta is not None:
            respuesta.close()


def _leer_fecha(segundos):
    """Convierte la fecha de actualización de la API (segundos Unix) a date."""
    if type(segundos) is not int or segundos <= 0:
        raise ValueError("La API no entregó una fecha válida.")
    try:
        return datetime.fromtimestamp(segundos, tz=timezone.utc).date()
    except (OverflowError, OSError, ValueError):
        raise ValueError("La fecha del indicador no tiene un formato válido.") from None


def _leer_valor(datos):
    """Obtiene el valor en pesos chilenos (CLP) y comprueba que sea un número válido."""
    tasas = datos.get("rates")
    if not isinstance(tasas, dict):
        raise ValueError("La API no entregó las tasas de cambio.")
    valor = tasas.get("CLP")
    if type(valor) not in (int, float):
        raise ValueError("El valor recibido para el indicador no es válido.")
    try:
        valor = float(valor)
    except OverflowError:
        raise ValueError("El valor recibido para el indicador no es válido.") from None
    if not math.isfinite(valor) or valor <= 0:
        raise ValueError("El valor recibido para el indicador no es válido.")
    return valor


def _validar_respuesta(datos, codigo_esperado):
    """Comprueba la estructura de una respuesta de ExchangeRate-API."""
    codigo_esperado = validar_codigo(codigo_esperado)
    if not isinstance(datos, dict):
        raise ValueError("La respuesta de la API debe ser un objeto JSON.")
    if datos.get("result") != "success":
        raise ValueError("La API no entregó una respuesta exitosa.")
    if datos.get("base_code") != MONEDAS[codigo_esperado]:
        raise ValueError("La API respondió con un indicador distinto al solicitado.")


def crear_indicadores(datos, codigo):
    """Convierte la respuesta de la API en una lista con el indicador (1 elemento)."""
    codigo = validar_codigo(codigo)
    _validar_respuesta(datos, codigo)
    indicador = Indicador(
        codigo=codigo,
        fecha=_leer_fecha(datos.get("time_last_update_unix")),
        valor=_leer_valor(datos),
        unidad="Pesos",
        fuente=FUENTE,
        verificado_en=datetime.now(),
    )
    return [indicador]


def crear_indicador(datos, codigo):
    """Convierte la respuesta de la API en un objeto Indicador."""
    return crear_indicadores(datos, codigo)[0]


def extraer_primero(datos, codigo_esperado="dolar"):
    """Devuelve la fecha y el valor del indicador de la respuesta."""
    indicador = crear_indicador(datos, codigo_esperado)
    return indicador.fecha.isoformat(), indicador.valor
