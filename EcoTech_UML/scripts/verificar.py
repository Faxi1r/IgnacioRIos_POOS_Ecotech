"""Ejecuta las pruebas y, si se pide, guarda lo que realmente ocurrió."""
import argparse
import io
import platform
import sqlite3
import sys
import unittest
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--guardar", type=Path, help="Archivo donde guardar el resultado")
    argumentos = parser.parse_args()
    salida = io.StringIO()
    salida.write(f"Revisión EcoTech - {datetime.now(timezone.utc).isoformat()}\n")
    salida.write(f"Python {platform.python_version()} | SQLite {sqlite3.sqlite_version}\n")
    salida.write(f"PyMySQL {version('PyMySQL')} | python-dotenv {version('python-dotenv')}\n")
    salida.write(f"cryptography {version('cryptography')} | reportlab {version('reportlab')} | openpyxl {version('openpyxl')}\n")
    salida.write(f"requests {version('requests')}\n")
    salida.write("Integración real: SQLite temporal por prueba. MySQL usa simulaciones del conector, no un servidor. HTTP se simula en las pruebas.\n\n")
    pruebas = unittest.defaultTestLoader.discover(str(RAIZ / "tests"), top_level_dir=str(RAIZ))
    resultado = unittest.TextTestRunner(stream=salida, verbosity=2).run(pruebas)
    texto = salida.getvalue()
    print(texto)
    if argumentos.guardar:
        argumentos.guardar.parent.mkdir(parents=True, exist_ok=True)
        argumentos.guardar.write_text(texto, encoding="utf-8")
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
