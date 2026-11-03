import io
import os
import shutil
import sqlite3
from contextlib import closing
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet
from dotenv import dotenv_values
from scripts.preparar_entorno import preparar_entorno
from src.demostracion import ejecutar_demostracion
from src.persistencia import DAOError, EmpleadoDAO, crear_tablas
from src.persistencia.semilla_bd import cargar_semilla
from tests.apoyo import BaseBD

RAIZ = Path(__file__).resolve().parents[1]


class IntegracionTest(BaseBD):
    def test_semilla_repetida_no_duplica_datos(self):
        with patch("sys.stdout", io.StringIO()):
            uno, dos = cargar_semilla(), cargar_semilla()
        self.assertEqual(uno, dos)
        self.assertEqual(
            uno,
            {
                "usuarios": 3,
                "empleados": 3,
                "departamentos": 1,
                "proyectos": 1,
                "registros": 2,
                "informes": 1,
            },
        )

    def test_demo_conserva_la_base_y_restaurar_configuracion(self):
        self.persona()
        anterior = self.base.read_bytes()
        configuracion = (os.environ["DB_NAME"], os.environ["DB_ENGINE"])
        with patch("sys.stdout", io.StringIO()):
            ejecutar_demostracion()
        self.assertEqual(self.base.read_bytes(), anterior)
        self.assertEqual((os.environ["DB_NAME"], os.environ["DB_ENGINE"]), configuracion)

    def test_otra_ejecucion_recupera_los_datos(self):
        self.persona(nombre="Persona Persistente")
        codigo = "from src.persistencia import EmpleadoDAO; print(EmpleadoDAO.listar()[0].nombre)"
        resultado = subprocess.run(
            [sys.executable, "-c", codigo], cwd=RAIZ, text=True, capture_output=True
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("Persona Persistente", resultado.stdout)

    def test_entrada_directa_funciona_desde_otra_carpeta(self):
        resultado = subprocess.run(
            [sys.executable, str(RAIZ / "src/main.py"), "--comprobar-conexion"],
            cwd=self.carpeta,
            text=True,
            capture_output=True,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("Motor: sqlite", resultado.stdout)

    def test_demo_y_login_por_consola_terminan_correctamente(self):
        resultado = subprocess.run(
            [sys.executable, "-m", "src.main", "--demo"], cwd=RAIZ, text=True, capture_output=True
        )
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
        self.assertIn("Demostración correcta", resultado.stdout)
        with patch("sys.stdout", io.StringIO()):
            cargar_semilla()
        resultado = subprocess.run(
            [sys.executable, "-m", "src.main"],
            cwd=RAIZ,
            text=True,
            input="admin_demo\nDemo2026*\n0\n",
            capture_output=True,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
        self.assertIn("Bienvenido, admin_demo", resultado.stdout)

    def test_base_antigua_se_rechaza_sin_borrarla(self):
        antigua = self.carpeta / "antigua.db"
        with closing(sqlite3.connect(antigua)) as conexion, conexion:
            conexion.execute("CREATE TABLE usuario (id_usuario INTEGER, nombre TEXT)")
            conexion.execute("INSERT INTO usuario VALUES (1, 'Conservar')")
        antes = antigua.read_bytes()
        with patch.dict(os.environ, {"DB_NAME": str(antigua)}), self.assertRaises(DAOError):
            crear_tablas()
        self.assertEqual(antigua.read_bytes(), antes)

    def test_script_env_genera_clave_valida_y_no_la_sobrescribe(self):
        shutil.copy2(RAIZ / ".env.example", self.carpeta / ".env.example")
        salida = io.StringIO()
        with patch("sys.stdout", salida):
            self.assertTrue(preparar_entorno(self.carpeta))
        contenido = (self.carpeta / ".env").read_text()
        clave = dotenv_values(self.carpeta / ".env")["ECOTECH_CLAVE_CIFRADO"]
        Fernet(clave.encode())
        self.assertNotIn(clave, salida.getvalue())
        with patch("sys.stdout", io.StringIO()):
            self.assertFalse(preparar_entorno(self.carpeta))
        self.assertEqual((self.carpeta / ".env").read_text(), contenido)
        with tempfile.TemporaryDirectory() as otra:
            shutil.copy2(RAIZ / ".env.example", Path(otra) / ".env.example")
            with patch("sys.stdout", io.StringIO()):
                preparar_entorno(otra)
            self.assertNotEqual(dotenv_values(Path(otra) / ".env")["ECOTECH_CLAVE_CIFRADO"], clave)
