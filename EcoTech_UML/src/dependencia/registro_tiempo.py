from datetime import date
from typing import Optional

from .validaciones import validar_fecha, validar_id, validar_numero, validar_texto


class RegistroDeTiempo:
    """Guarda cuándo, cuánto y en qué proyecto trabajó un empleado."""

    def __init__(
        self,
        id_registro: Optional[int],
        fecha: date,
        horas: float,
        descripcion_tareas: str,
        id_empleado: Optional[int] = None,
        id_proyecto: Optional[int] = None,
    ) -> None:
        self.id_registro = validar_id(id_registro, opcional=True)
        self.fecha = fecha
        self.horas = horas
        self.descripcion_tareas = descripcion_tareas
        self.id_empleado = validar_id(id_empleado, "El id del empleado", opcional=True)
        self.id_proyecto = validar_id(id_proyecto, "El id del proyecto", opcional=True)
        self.validar_datos()

    def validar_datos(self) -> None:
        self.fecha = self._fecha
        self.horas = self._horas
        self.descripcion_tareas = self._descripcion_tareas

    @property
    def fecha(self) -> date:
        return self._fecha

    @fecha.setter
    def fecha(self, valor: date) -> None:
        self._fecha = validar_fecha(valor, "La fecha del registro")

    @property
    def horas(self) -> float:
        return self._horas

    @horas.setter
    def horas(self, valor: float) -> None:
        self._horas = validar_numero(valor, "Las horas", minimo=0, maximo=24, minimo_exclusivo=True, decimales=2)

    @property
    def descripcion_tareas(self) -> str:
        return self._descripcion_tareas

    @descripcion_tareas.setter
    def descripcion_tareas(self, valor: str) -> None:
        self._descripcion_tareas = validar_texto(valor, "La descripción de tareas", 500)

    def __str__(self) -> str:
        return (
            f"RegistroDeTiempo(id={self.id_registro}, fecha={self.fecha}, horas={self.horas}, "
            f"empleado={self.id_empleado}, proyecto={self.id_proyecto})"
        )
