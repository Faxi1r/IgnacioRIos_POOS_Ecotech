import os
import sqlite3
import unittest
from unittest.mock import MagicMock, patch
from cryptography.fernet import Fernet
from src.dependencia import Seguridad

from src.persistencia import ConexionError, DAOError, DAOIntegridadError
from src.persistencia import conexion
from src.persistencia.crear_bd import crear_tablas
from src.persistencia.dao_util import sesion_bd


class ConexionTest(unittest.TestCase):
    def test_configuracion_mysql_se_envia_al_conector_sin_reemplazar_el_motor(self):
        entorno = {
            "DB_ENGINE": "mysql",
            "DB_NAME": "ecotech_prueba",
            "DB_HOST": "127.0.0.1",
            "DB_PORT": "3307",
            "DB_USER": "estudiante",
            "DB_PASSWORD": "clave_ficticia",
        }
        with patch.dict(os.environ, entorno), patch.object(conexion.pymysql, "connect") as conectar:
            conexion.abrir_conexion()
            argumentos = conectar.call_args.kwargs
        self.assertEqual(argumentos["port"], 3307)
        self.assertEqual(argumentos["database"], "ecotech_prueba")
        self.assertEqual(argumentos["user"], "estudiante")
        self.assertFalse(argumentos["autocommit"])

    def test_error_mysql_no_recurre_a_sqlite(self):
        with patch.dict(os.environ, {"DB_ENGINE": "mysql"}), patch.object(
            conexion.pymysql,
            "connect",
            side_effect=conexion.pymysql.err.OperationalError(2003, "Fallo"),
        ), patch.object(conexion.sqlite3, "connect") as sqlite:
            with self.assertRaisesRegex(ConexionError, "No se cambió a SQLite"):
                conexion.abrir_conexion()
            sqlite.assert_not_called()

    def test_motor_desconocido_se_rechaza(self):
        with patch.dict(os.environ, {"DB_ENGINE": "otro"}):
            with self.assertRaises(ConexionError):
                conexion.abrir_conexion()

    def test_ruta_sqlite_relativa_usa_la_raiz_del_proyecto(self):
        with patch.dict(os.environ, {"DB_NAME": "ecotech_u2.db"}):
            self.assertEqual(conexion._ruta_sqlite(), str(conexion.RAIZ_PROYECTO / "ecotech_u2.db"))

    def test_marcadores_de_cada_motor(self):
        for motor, esperado in [("sqlite", "?"), ("mysql", "%s")]:
            with self.subTest(motor=motor), patch.dict(os.environ, {"DB_ENGINE": motor}):
                self.assertEqual(conexion.marcador_sql(), esperado)

    def test_creacion_mysql_no_desactiva_claves_y_completa_fk_del_gerente(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        cursor.fetchone.return_value = None
        with patch("src.persistencia.crear_bd.obtener_motor", return_value="mysql"), patch(
            "src.persistencia.crear_bd.sesion_bd"
        ) as sesion, patch.dict(
            os.environ, {"ECOTECH_CLAVE_CIFRADO": Fernet.generate_key().decode()}
        ):
            sesion.return_value.__enter__.return_value = cursor
            crear_tablas()
        sentencias = [llamada.args[0] for llamada in cursor.execute.call_args_list]
        self.assertFalse(any("FOREIGN_KEY_CHECKS" in sql for sql in sentencias))
        posicion_fk = next(
            i for i, sql in enumerate(sentencias) if "ALTER TABLE departamento" in sql
        )
        self.assertLess(
            next(
                i
                for i, sql in enumerate(sentencias)
                if "CREATE TABLE IF NOT EXISTS empleado" in sql
            ),
            posicion_fk,
        )

    def test_fk_mysql_no_se_agrega_de_nuevo_si_ya_existe(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = [("id_usuario",), ("activo",), ("rol",)]
        with patch("src.persistencia.crear_bd.obtener_motor", return_value="mysql"), patch(
            "src.persistencia.crear_bd.sesion_bd"
        ) as sesion, patch.dict(
            os.environ, {"ECOTECH_CLAVE_CIFRADO": Fernet.generate_key().decode()}
        ):
            cursor.fetchone.side_effect = [(1,), (Seguridad().cifrar("EcoTech UML 8"),)]
            sesion.return_value.__enter__.return_value = cursor
            crear_tablas()
        self.assertFalse(
            any("ALTER TABLE" in llamada.args[0] for llamada in cursor.execute.call_args_list)
        )


class TransaccionTest(unittest.TestCase):
    def test_exito_confirma_y_cierra(self):
        conexion_falsa = MagicMock()
        with patch("src.persistencia.dao_util.abrir_conexion", return_value=conexion_falsa):
            with sesion_bd() as cursor:
                cursor.execute("Una operación de prueba")
        conexion_falsa.commit.assert_called_once()
        conexion_falsa.rollback.assert_not_called()
        conexion_falsa.cursor.return_value.close.assert_called_once()
        conexion_falsa.close.assert_called_once()

    def test_integridad_revierte_no_confirma_y_cierra(self):
        conexion_falsa = MagicMock()
        conexion_falsa.cursor.return_value.execute.side_effect = sqlite3.IntegrityError(
            "UNIQUE constraint failed"
        )
        with patch("src.persistencia.dao_util.abrir_conexion", return_value=conexion_falsa):
            with self.assertRaises(DAOIntegridadError), sesion_bd() as cursor:
                cursor.execute("Una operación de prueba")
        conexion_falsa.rollback.assert_called_once()
        conexion_falsa.commit.assert_not_called()
        conexion_falsa.cursor.return_value.close.assert_called_once()
        conexion_falsa.close.assert_called_once()

    def test_fallo_al_confirmar_tambien_revierte(self):
        conexion_falsa = MagicMock()
        conexion_falsa.commit.side_effect = sqlite3.OperationalError("Fallo de prueba")
        with patch("src.persistencia.dao_util.abrir_conexion", return_value=conexion_falsa):
            with self.assertRaises(DAOError), sesion_bd():
                pass
        conexion_falsa.rollback.assert_called_once()
        conexion_falsa.close.assert_called_once()
