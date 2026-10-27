"""Contraseñas y cifrado de los datos que se guardan."""
import base64
import hashlib
import hmac
import secrets

from cryptography.fernet import Fernet, InvalidToken
from src.configuracion import clave_cifrado
from .validaciones import validar_contrasena


class Seguridad:
    def hashear_contrasena(self, contrasena: str) -> str:
        validar_contrasena(contrasena)
        sal = secrets.token_bytes(16)
        resultado = hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf-8"), sal, 600_000)
        return "pbkdf2_sha256$600000$" + sal.hex() + "$" + resultado.hex()

    def verificar_contrasena(self, contrasena: str, hash_guardado: str) -> bool:
        if not isinstance(contrasena, str) or not isinstance(hash_guardado, str):
            return False
        try:
            algoritmo, iteraciones, sal, esperado = hash_guardado.split("$")
            if algoritmo != "pbkdf2_sha256" or iteraciones != "600000":
                return False
            sal, esperado = bytes.fromhex(sal), bytes.fromhex(esperado)
            if len(sal) != 16 or len(esperado) != 32:
                return False
            resultado = hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf-8"), sal, 600_000)
            return hmac.compare_digest(resultado, esperado)
        except (ValueError, TypeError):
            return False

    def _cifrador(self):
        clave = clave_cifrado()
        try:
            return Fernet(clave)
        except (ValueError, UnicodeError) as error:
            raise ValueError("Revise ECOTECH_CLAVE_CIFRADO en .env; debe ser una clave Fernet válida.") from error

    def cifrar(self, dato: str) -> str:
        if not isinstance(dato, str):
            raise ValueError("El dato que se va a cifrar debe ser texto.")
        return self._cifrador().encrypt(dato.encode("utf-8")).decode("ascii")

    def descifrar(self, dato_cifrado: str) -> str:
        try:
            return self._cifrador().decrypt(dato_cifrado.encode("ascii")).decode("utf-8")
        except (InvalidToken, UnicodeError, AttributeError) as error:
            raise ValueError("No se pudo leer el dato cifrado. Revise la clave original y la integridad de la base.") from error

    def _indice_busqueda(self, campo, valor):
        # Permite detectar duplicados sin dejar el correo o la identificación visibles.
        self._cifrador()
        clave = base64.urlsafe_b64decode(clave_cifrado())
        clave_indice = hmac.new(clave, b"EcoTech indices v1", hashlib.sha256).digest()
        return hmac.new(clave_indice, f"{campo}:{valor}".encode("utf-8"), hashlib.sha256).hexdigest()
