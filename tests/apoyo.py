import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet
from src.dependencia import Administrador, Empleado, Proyecto, Seguridad, Usuario
from src.persistencia import EmpleadoDAO, ProyectoDAO, UsuarioDAO, crear_tablas

CLAVE = "Prueba2026*"
HASH_PRUEBA = Seguridad().hashear_contrasena(CLAVE)


def empleado(numero=1, **cambios):
    datos = dict(
        id_empleado=None,
        identificacion=f"EMP{numero:04d}",
        nombre=f"Persona {numero}",
        correo=f"persona{numero}@ejemplo.cl",
        salario=900000,
        direccion="Calle de Prueba 123",
        telefono="+56 912345678",
        fecha_inicio_contrato=date(2026, 3, 1),
    )
    datos.update(cambios)
    return Empleado(**datos)


class BaseBD(unittest.TestCase):
    """Cada prueba abre una base temporal con su propia clave."""

    def setUp(self):
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.carpeta = Path(carpeta.name)
        self.base = self.carpeta / "prueba.db"
        entorno = patch.dict(
            os.environ,
            {
                "DB_ENGINE": "sqlite",
                "DB_NAME": str(self.base),
                "ECOTECH_CLAVE_CIFRADO": Fernet.generate_key().decode("ascii"),
            },
        )
        entorno.start()
        self.addCleanup(entorno.stop)
        crear_tablas()

    def cuenta(self, nombre="ana_prueba", admin=False):
        clase = Administrador if admin else Usuario
        return UsuarioDAO.insertar(clase(None, nombre, HASH_PRUEBA))

    def persona(self, numero=1, **cambios):
        return EmpleadoDAO.insertar(empleado(numero, **cambios))

    def proyecto(self, nombre="Sensores"):
        return ProyectoDAO.insertar(Proyecto(None, nombre, "Medir el consumo", date(2026, 3, 1)))

    def sesion(self, cuenta=None, numero=99):
        from src.servicios.autenticacion import autenticar

        cuenta = cuenta or self.cuenta("admin_formularios", admin=True)
        persona = self.persona(numero)
        EmpleadoDAO.vincular_cuenta(persona.id_empleado, cuenta.id_usuario)
        return autenticar(cuenta.nombre_usuario, CLAVE)
