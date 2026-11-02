"""Reglas que comparten las clases y los menús para revisar los datos."""
import math
import re
from datetime import date, datetime
from typing import Any, Optional

PATRON_TELEFONO = re.compile(r"^[0-9+\-()\s]{6,20}$")


def validar_texto(valor: Any, campo: str, largo_maximo: int = 255) -> str:
    """Texto obligatorio: sin espacios sobrantes, no vacío y dentro del largo permitido."""
    if not isinstance(valor, str):
        raise ValueError(f"{campo} debe ser un texto.")
    limpio = valor.strip()
    if not limpio:
        raise ValueError(f"{campo} no puede estar vacío.")
    if len(limpio) > largo_maximo:
        raise ValueError(f"{campo} no puede superar {largo_maximo} caracteres.")
    return limpio


def validar_texto_opcional(valor: Any, campo: str, largo_maximo: int = 255) -> str:
    """Texto que puede quedar vacío ('' si no se informa), pero si se informa debe ser válido."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return ""
    return validar_texto(valor, campo, largo_maximo)


def validar_nombre_usuario(valor: Any) -> str:
    nombre = validar_texto(valor, "El nombre de usuario", 40).lower()
    if not re.fullmatch(r"[a-z0-9_.-]{3,40}", nombre):
        raise ValueError("Use de 3 a 40 letras, números, puntos, guiones o guiones bajos.")
    return nombre


def validar_identificacion(valor: Any) -> str:
    texto = validar_texto(valor, "La identificación", 60).upper()
    # Se guarda igual aunque se escriba con puntos, guiones o espacios.
    limpio = re.sub(r"[.\s-]", "", texto)
    if not re.fullmatch(r"[A-Z0-9]{4,30}", limpio):
        raise ValueError("La identificación debe tener entre 4 y 30 letras o números.")
    return limpio


def validar_telefono(valor: Any) -> str:
    """Teléfono opcional: dígitos, espacios y los símbolos + - ( )."""
    limpio = validar_texto_opcional(valor, "El teléfono", 20)
    if limpio and (not PATRON_TELEFONO.fullmatch(limpio) or sum(c.isdigit() for c in limpio) < 6):
        raise ValueError("Ingrese un teléfono con al menos 6 números y hasta 20 caracteres; puede usar + - ( ) y espacios.")
    return limpio


def validar_contrasena(valor: Any) -> str:
    """Contraseña de al menos 8 caracteres con letras y números."""
    if not isinstance(valor, str) or len(valor) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")
    if not any(c.isalpha() for c in valor) or not any(c.isdigit() for c in valor):
        raise ValueError("La contraseña debe incluir letras y números.")
    return valor


def validar_numero(
    valor: Any,
    campo: str,
    minimo: Optional[float] = None,
    maximo: Optional[float] = None,
    minimo_exclusivo: bool = False,
    decimales: Optional[int] = None,
) -> float:
    """
    Número finito dentro de un rango. Rechaza booleanos (True se comporta como 1 en Python),
    texto no numérico y también 'nan' / 'inf', que float() acepta y romperían las comparaciones.
    """
    if isinstance(valor, bool):
        raise ValueError(f"{campo} no puede ser un valor booleano.")
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{campo} debe ser un valor numérico.") from None
    if not math.isfinite(numero):
        raise ValueError(f"{campo} debe ser un número finito.")
    if minimo is not None:
        if minimo_exclusivo and numero <= minimo:
            raise ValueError(f"{campo} debe ser mayor que {minimo:g}.")
        if not minimo_exclusivo and numero < minimo:
            raise ValueError(f"{campo} no puede ser menor que {minimo:g}.")
    if maximo is not None and numero > maximo:
        raise ValueError(f"{campo} no puede superar {maximo:g}.")
    if decimales is not None and not math.isclose(numero, round(numero, decimales), rel_tol=0, abs_tol=1e-9):
        raise ValueError(f"{campo} admite hasta {decimales} decimales.")
    return numero


def validar_id(valor: Any, campo: str = "El id", opcional: bool = False) -> Optional[int]:
    """Los ids son enteros positivos; None se usa antes de guardar un objeto."""
    if valor is None and opcional:
        return None
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise ValueError(f"{campo} debe ser un número entero mayor que cero.")
    return valor


def validar_fecha(valor: Any, campo: str, opcional: bool = False) -> Optional[date]:
    """Fecha de tipo date (un datetime se reduce a su fecha)."""
    if valor is None:
        if opcional:
            return None
        raise ValueError(f"{campo} es obligatoria.")
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    raise ValueError(f"{campo} debe ser una fecha válida.")
