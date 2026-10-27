import json
from datetime import date
from typing import Optional

from .registro_tiempo import RegistroDeTiempo
from .seguridad import Seguridad
from .usuario import Usuario
from .validaciones import (
    validar_fecha, validar_id, validar_identificacion,
    validar_numero, validar_telefono, validar_texto,
)


class Empleado:
    """Ficha del trabajador, con una cuenta opcional."""

    MIN_NOMBRE = 2
    MAX_NOMBRE = 100
    MIN_CORREO = 6
    MAX_CORREO = 254

    @classmethod
    def validar_nombre(cls, nombre):
        if not isinstance(nombre, str):
            raise TypeError("El nombre debe ser texto.")
        nombre = nombre.strip()
        if not cls.MIN_NOMBRE <= len(nombre) <= cls.MAX_NOMBRE:
            raise ValueError(
                f"El nombre debe tener entre {cls.MIN_NOMBRE} "
                f"y {cls.MAX_NOMBRE} caracteres."
            )
        return nombre

    @classmethod
    def validar_correo(cls, correo):
        if not isinstance(correo, str):
            raise TypeError("El correo debe ser texto.")
        correo = correo.strip().lower()
        if not cls.MIN_CORREO <= len(correo) <= cls.MAX_CORREO:
            raise ValueError("Correo fuera del largo permitido.")
        if any(c.isspace() for c in correo):
            raise ValueError("El correo no debe contener espacios.")
        if correo.count("@") != 1:
            raise ValueError("El correo debe contener un solo @.")
        usuario, dominio = correo.split("@")
        if not usuario or "." not in dominio:
            raise ValueError("Use un correo como nombre@empresa.cl.")
        if any(not parte for parte in dominio.split(".")):
            raise ValueError("El dominio contiene puntos inválidos.")
        return correo

    def __init__(self, id_empleado: Optional[int], identificacion: str, nombre: str,
                 correo: str, salario: float, direccion: str, telefono: str,
                 fecha_inicio_contrato: date, usuario: Optional[Usuario] = None):
        self.id_empleado = validar_id(id_empleado, opcional=True)
        self._identificacion, self._nombre, self._correo = identificacion, nombre, correo
        self._salario, self._direccion, self._telefono = salario, direccion, telefono
        self._fecha_inicio_contrato = fecha_inicio_contrato
        if usuario is not None and not isinstance(usuario, Usuario):
            raise ValueError("La cuenta debe ser un Usuario.")
        self._usuario = usuario
        self._departamento = None
        self._id_departamento = None
        self._registros_tiempo = []
        self.validar_datos()

    @property
    def identificacion(self):
        return self._identificacion

    @identificacion.setter
    def identificacion(self, valor):
        self._identificacion = validar_identificacion(valor)

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        self._nombre = self.validar_nombre(valor)

    @property
    def correo(self):
        return self._correo

    @correo.setter
    def correo(self, valor):
        self._correo = self.validar_correo(valor)

    @property
    def salario(self):
        return self._salario

    @salario.setter
    def salario(self, valor):
        self._salario = validar_numero(valor, "El salario", minimo=0, maximo=9999999999.99, decimales=2)

    @property
    def direccion(self):
        return self._direccion

    @direccion.setter
    def direccion(self, valor):
        self._direccion = validar_texto(valor, "La dirección", 255)

    @property
    def telefono(self):
        return self._telefono

    @telefono.setter
    def telefono(self, valor):
        self._telefono = validar_telefono(validar_texto(valor, "El teléfono", 20))

    @property
    def fecha_inicio_contrato(self):
        return self._fecha_inicio_contrato

    @fecha_inicio_contrato.setter
    def fecha_inicio_contrato(self, valor):
        self._fecha_inicio_contrato = validar_fecha(valor, "La fecha de inicio de contrato")

    @property
    def usuario(self):
        return self._usuario

    @property
    def departamento(self):
        return self._departamento

    @property
    def id_departamento(self):
        return self.departamento.id_departamento if self.departamento else self._id_departamento

    @property
    def registros_tiempo(self):
        return list(self._registros_tiempo)

    def validar_datos(self) -> None:
        self.identificacion = self._identificacion
        self.nombre = self._nombre
        self.correo = self._correo
        self.salario = self._salario
        self.direccion = self._direccion
        self.telefono = self._telefono
        self.fecha_inicio_contrato = self._fecha_inicio_contrato

    def registrar_horas(self, fecha: date, proyecto: "Proyecto", horas: float,
                        descripcion: str) -> RegistroDeTiempo:
        from .proyecto import Proyecto
        if not isinstance(proyecto, Proyecto) or self not in proyecto.empleados_asignados:
            raise ValueError("Asigne primero al empleado a ese proyecto.")
        registro = RegistroDeTiempo(None, fecha, horas, descripcion, self.id_empleado, proyecto.id_proyecto)
        self._registros_tiempo.append(registro)
        proyecto._registros_tiempo.append(registro)
        return registro

    def _cifrar_datos(self):
        self.validar_datos()
        datos = {"identificacion": self.identificacion, "nombre": self.nombre,
                 "correo": self.correo, "salario": self.salario, "direccion": self.direccion,
                 "telefono": self.telefono, "fecha_inicio_contrato": self.fecha_inicio_contrato.isoformat()}
        return Seguridad().cifrar(json.dumps(datos, ensure_ascii=False))

    def __eq__(self, otro):
        if not isinstance(otro, Empleado):
            return NotImplemented
        return self is otro or (self.id_empleado is not None and self.id_empleado == otro.id_empleado)

    __hash__ = None

    def __str__(self):
        return f"Empleado(id={self.id_empleado}, identificación='{self.identificacion}', nombre='{self.nombre}')"
