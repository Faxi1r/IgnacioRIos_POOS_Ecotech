import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


class ArquitecturaTest(unittest.TestCase):
    def test_hay_una_sola_carpeta_de_clases(self):
        self.assertTrue((RAIZ / "src" / "dependencia").is_dir())
        for carpeta in ("dominio", "servicios", "controllers", "repositories"):
            self.assertFalse((RAIZ / "src" / carpeta).exists())

    def test_dominio_no_importa_persistencia_ni_conectores(self):
        for archivo in (RAIZ / "src" / "dependencia").glob("*.py"):
            texto = archivo.read_text(encoding="utf-8")
            for importacion in ("from src.persistencia", "import sqlite3", "import pymysql"):
                self.assertNotIn(importacion, texto, archivo.name)

    def test_main_y_menus_no_abren_conexiones_ni_ejecutan_sql(self):
        archivos = [RAIZ / "src" / "main.py", *(RAIZ / "src" / "menus").glob("*.py")]
        for archivo in archivos:
            texto = archivo.read_text(encoding="utf-8")
            for llamada in (".execute(", ".cursor(", ".connect("):
                self.assertNotIn(llamada, texto, archivo.name)

    def test_configuracion_local_no_se_publica(self):
        ignorados = (RAIZ / ".gitignore").read_text(encoding="utf-8").splitlines()
        for nombre in (".env", ".venv/", "__pycache__/", "*.db"):
            self.assertIn(nombre, ignorados)
        self.assertTrue((RAIZ / ".env.example").exists())
