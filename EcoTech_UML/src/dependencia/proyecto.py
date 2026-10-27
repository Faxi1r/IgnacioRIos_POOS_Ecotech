from datetime import date
from typing import List, Optional

from .empleado import Empleado
from .registro_tiempo import RegistroDeTiempo
from .validaciones import validar_fecha, validar_id, validar_texto


class Proyecto:
    """Proyecto con sus empleados asignados y las horas que han trabajado."""

    def __init__(
        self,
        id_proyecto: Optional[int],
        nombre: str,
        descripcion: str,
        fecha_inicio: date,
        empleados_asignados: Optional[List[Empleado]] = None,
    ) -> None:
        self.id_proyecto = validar_id(id_proyecto, opcional=True)
        self.nombre = nombre
        self.descripcion = descripcion
        self.fecha_inicio = fecha_inicio
        self._empleados_asignados: List[Empleado] = []
        for empleado in empleados_asignados or []:
            self.asignar_empleado(empleado)
        self._registros_tiempo: List[RegistroDeTiempo] = []
        self.validar_datos()

    def validar_datos(self) -> None:
        self.nombre = self._nombre
        self.descripcion = self._descripcion
        self.fecha_inicio = self._fecha_inicio

    @property
    def empleados_asignados(self) -> List[Empleado]:
        return list(self._empleados_asignados)

    @property
    def registros_tiempo(self) -> List[RegistroDeTiempo]:
        return list(self._registros_tiempo)

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self._nombre = validar_texto(valor, "El nombre del proyecto", 150)

    @property
    def descripcion(self) -> str:
        return self._descripcion

    @descripcion.setter
    def descripcion(self, valor: str) -> None:
        self._descripcion = validar_texto(valor, "La descripción del proyecto", 500)

    @property
    def fecha_inicio(self) -> date:
        return self._fecha_inicio

    @fecha_inicio.setter
    def fecha_inicio(self, valor: date) -> None:
        self._fecha_inicio = validar_fecha(valor, "La fecha de inicio")

    def asignar_empleado(self, empleado: Empleado) -> None:
        """Agrega al empleado solo si todavía no está asignado."""
        if not isinstance(empleado, Empleado):
            raise ValueError("Debe indicar un Empleado válido.")
        if empleado not in self._empleados_asignados:
            self._empleados_asignados.append(empleado)

    def desasignar_empleado(self, empleado: Empleado) -> None:
        """Quita la asignación, pero conserva las horas anteriores."""
        if empleado in self._empleados_asignados:
            self._empleados_asignados.remove(empleado)

    def __str__(self) -> str:
        return (
            f"Proyecto(id={self.id_proyecto}, nombre='{self.nombre}', inicio={self.fecha_inicio}, "
            f"empleados={len(self.empleados_asignados)})"
        )
