from typing import Optional

from .empleado import Empleado
from .validaciones import validar_id, validar_texto


class Departamento:
    """Tiene al menos un empleado: su gerente."""

    def __init__(self, id_departamento: Optional[int], nombre: str, gerente: Empleado, empleados=None):
        self.id_departamento = validar_id(id_departamento, opcional=True)
        self.nombre = nombre
        self._empleados = []
        self._gerente = None
        # Revisamos a todos antes de cambiar la pertenencia de cualquiera.
        for empleado in [gerente, *(empleados or [])]:
            self._revisar_pertenencia(empleado)
        for empleado in empleados or []:
            self.agregar_empleado(empleado)
        self.asignar_gerente(gerente)
        self.validar_datos()

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        self._nombre = validar_texto(valor, "El nombre del departamento", 100)

    @property
    def gerente(self):
        return self._gerente

    @property
    def empleados(self):
        return list(self._empleados)

    def validar_datos(self) -> None:
        self.nombre = self._nombre
        if not isinstance(self.gerente, Empleado) or self.gerente not in self._empleados:
            raise ValueError("El departamento necesita un gerente que pertenezca a sus empleados.")
        for empleado in self._empleados:
            if empleado.departamento is not self:
                raise ValueError("Revise la pertenencia de los empleados al departamento.")

    def _revisar_pertenencia(self, empleado):
        if not isinstance(empleado, Empleado):
            raise ValueError("Debe indicar un empleado válido.")
        if empleado.departamento is not None and empleado.departamento is not self:
            if self.id_departamento is None or empleado.id_departamento != self.id_departamento:
                raise ValueError("Quite primero al empleado de su departamento actual.")
        if empleado.id_departamento is not None and empleado.id_departamento != self.id_departamento:
            raise ValueError("El empleado ya pertenece a otro departamento.")

    def agregar_empleado(self, empleado: Empleado) -> None:
        self._revisar_pertenencia(empleado)
        if empleado not in self._empleados:
            self._empleados.append(empleado)
        empleado._departamento = self
        empleado._id_departamento = self.id_departamento

    def quitar_empleado(self, empleado: Empleado) -> None:
        if empleado == self.gerente:
            raise ValueError("Designe a otro gerente antes de quitar al actual.")
        for actual in self._empleados:
            if actual == empleado:
                self._empleados.remove(actual)
                actual._departamento = None
                actual._id_departamento = None
                return

    def asignar_gerente(self, empleado: Empleado) -> None:
        self.agregar_empleado(empleado)
        self._gerente = next(persona for persona in self._empleados if persona == empleado)

    def __str__(self):
        return (f"Departamento(id={self.id_departamento}, nombre='{self.nombre}', "
                f"gerente='{self.gerente.nombre}', empleados={len(self._empleados)})")
