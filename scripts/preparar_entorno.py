"""Prepara la configuración local sin reemplazar una clave existente."""
import os
from pathlib import Path

from cryptography.fernet import Fernet

RAIZ = Path(__file__).resolve().parents[1]


def preparar_entorno(raiz=RAIZ):
    raiz = Path(raiz)
    destino = raiz / ".env"
    if destino.exists():
        print("El archivo .env ya existe. Se conserva tal como está.")
        return False
    plantilla = (raiz / ".env.example").read_text(encoding="utf-8")
    clave = Fernet.generate_key().decode("ascii")
    contenido = plantilla.replace("GENERAR_CON_EL_SCRIPT", clave)
    # La clave queda en el archivo local, sin mostrarse en pantalla.
    descriptor = os.open(destino, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)
    print("Archivo .env listo. Puede iniciar EcoTech.")
    return True


if __name__ == "__main__":
    preparar_entorno()
