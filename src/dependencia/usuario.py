from typing import Optional

from .seguridad import Seguridad
from .validaciones import validar_id, validar_nombre_usuario


class Usuario:
    """Una cuenta común puede trabajar con sus propios datos."""

    def __init__(self, id_usuario: Optional[int], nombre_usuario: str,
                 contrasena_hash: str = "", activo: bool = True):
        self.id_usuario = validar_id(id_usuario, opcional=True)
        self.nombre_usuario = nombre_usuario
        if not isinstance(contrasena_hash, str):
            raise ValueError("La contraseña guardada debe ser texto.")
        if not isinstance(activo, bool):
            raise ValueError("El estado de la cuenta debe ser verdadero o falso.")
        self._contrasena_hash = contrasena_hash
        self._activo = activo

    @property
    def nombre_usuario(self):
        return self._nombre_usuario

    @nombre_usuario.setter
    def nombre_usuario(self, valor):
        self._nombre_usuario = validar_nombre_usuario(valor)

    @property
    def contrasena_hash(self):
        return self._contrasena_hash

    @property
    def activo(self):
        return self._activo

    def establecer_contrasena(self, contrasena: str) -> None:
        self._contrasena_hash = Seguridad().hashear_contrasena(contrasena)

    def autenticar(self, contrasena: str) -> bool:
        return self.activo and Seguridad().verificar_contrasena(contrasena, self.contrasena_hash)

    def puede_acceder(self, modulo: str) -> bool:
        return self.activo and modulo == "mi_cuenta"

    def desactivar(self) -> None:
        self._activo = False

    def __str__(self):
        estado = "activa" if self.activo else "desactivada"
        return f"{type(self).__name__}(id={self.id_usuario}, usuario='{self.nombre_usuario}', {estado})"
