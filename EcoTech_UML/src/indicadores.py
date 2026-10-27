"""Consulta del dólar y revisión de los datos recibidos."""
import math
from datetime import datetime
import requests

URL_DOLAR = "https://mindicador.cl/api/dolar"


def obtener_datos():
    respuesta = requests.get(URL_DOLAR, timeout=(3, 5))
    respuesta.raise_for_status()
    return respuesta.json()


def extraer_primero(datos):
    if not isinstance(datos, dict):
        raise ValueError("Respuesta inesperada.")
    if datos.get("codigo") != "dolar":
        raise ValueError("La respuesta no corresponde al dólar.")
    if datos.get("unidad_medida") != "Pesos":
        raise ValueError("La unidad del indicador no es la esperada.")
    serie = datos.get("serie")
    if not isinstance(serie, list) or not serie:
        raise ValueError("No hay valores disponibles.")
    registro = serie[0]
    if not isinstance(registro, dict):
        raise ValueError("El registro del indicador no es válido.")
    valor = registro.get("valor")
    if type(valor) not in (int, float) or not math.isfinite(valor) or valor <= 0:
        raise ValueError("Valor del indicador inválido.")
    fecha = registro.get("fecha")
    if not isinstance(fecha, str):
        raise ValueError("Falta la fecha del indicador.")
    try:
        fecha = datetime.fromisoformat(fecha.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("La fecha del indicador no es válida.") from None
    return fecha.date().isoformat(), valor
