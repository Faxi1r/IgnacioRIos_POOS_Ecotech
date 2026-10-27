"""Configuración local compartida por la conexión y el cifrado."""
import os
from pathlib import Path
from dotenv import load_dotenv

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
load_dotenv(RAIZ_PROYECTO / ".env", override=False)


def clave_cifrado():
    clave = os.getenv("ECOTECH_CLAVE_CIFRADO", "").strip()
    if not clave or clave == "GENERAR_CON_EL_SCRIPT":
        raise ValueError("Falta ECOTECH_CLAVE_CIFRADO. Ejecute python scripts/preparar_entorno.py.")
    return clave.encode("ascii")
