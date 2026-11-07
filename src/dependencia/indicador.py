"""Representa un indicador financiero obtenido desde una API."""
from dataclasses import dataclass
from datetime import date, datetime
import math


@dataclass(frozen=True)
class Indicador:
    """Valor de un indicador expresado en pesos chilenos."""

    codigo: str
    fecha: date
    valor: float
    unidad: str = "Pesos"
    fuente: str = "open.er-api.com"
    verificado_en: datetime | None = None

    def __post_init__(self):
        """Evita crear objetos con datos que no se puedan guardar correctamente."""
        if self.codigo not in ("dolar", "euro"):
            raise ValueError("El código del indicador no es válido.")
        if type(self.fecha) is not date:
            raise ValueError("La fecha del indicador debe ser una fecha válida.")
        if type(self.valor) not in (int, float):
            raise ValueError("El valor del indicador debe ser numérico.")
        try:
            valor = float(self.valor)
        except (OverflowError, ValueError):
            raise ValueError("El valor del indicador no es válido.") from None
        if not math.isfinite(valor) or valor <= 0:
            raise ValueError("El valor del indicador debe ser mayor que cero.")
        if not isinstance(self.unidad, str) or self.unidad.strip().lower() != "pesos":
            raise ValueError("La unidad del indicador debe ser pesos chilenos.")
        if not isinstance(self.fuente, str) or not self.fuente.strip():
            raise ValueError("La fuente del indicador es obligatoria.")
        if self.verificado_en is not None and not isinstance(self.verificado_en, datetime):
            raise ValueError("La fecha de verificación no es válida.")
        object.__setattr__(self, "valor", valor)
        object.__setattr__(self, "unidad", "Pesos")
        object.__setattr__(self, "fuente", self.fuente.strip())
