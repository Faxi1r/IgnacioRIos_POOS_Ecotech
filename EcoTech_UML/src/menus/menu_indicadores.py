"""Presenta la referencia del dólar sin guardar datos nuevos."""
import requests
from src.indicadores import URL_DOLAR, obtener_datos, extraer_primero


def consultar_dolar():
    try:
        datos = obtener_datos()
        fecha, valor = extraer_primero(datos)
    except requests.exceptions.RequestException:
        print("No pudimos consultar el servicio. Reintente más tarde.")
    except (ValueError, KeyError, TypeError) as error:
        print(f"No se pudo usar el indicador: {error}")
    else:
        print(f"Dólar observado: {valor:.2f} CLP por USD")
        print(f"Fecha del registro: {fecha}")
        print(f"Origen: {URL_DOLAR}")
