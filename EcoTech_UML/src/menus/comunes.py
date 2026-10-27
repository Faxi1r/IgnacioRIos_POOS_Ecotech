"""Preguntas y mensajes que se repiten en varios menús."""
import getpass
import logging
import re
from datetime import date
from pathlib import Path

from src.dependencia import Empleado
from src.dependencia.validaciones import (
    validar_contrasena, validar_identificacion, validar_nombre_usuario,
    validar_numero, validar_texto, validar_texto_opcional,
)
from src.persistencia import ConexionError, DAOError, EmpleadoDAO, UsuarioDAO
from src.persistencia.conexion import RAIZ_PROYECTO


def pedir_con_validacion(mensaje, validador, secreto=False):
    while True:
        texto = getpass.getpass(mensaje) if secreto else input(mensaje)
        try:
            return validador(texto)
        except (TypeError, ValueError) as error:
            print(f"  {error}")


def pedir_texto(mensaje, campo, largo=100, opcional=False):
    validar = validar_texto_opcional if opcional else validar_texto
    return pedir_con_validacion(mensaje, lambda texto: validar(texto, campo, largo))


def entero_positivo(texto):
    texto = texto.strip()
    if not texto.isascii() or not texto.isdigit() or not 0 < int(texto) <= 2147483647:
        raise ValueError("Ingrese un id entero mayor que cero, sin letras ni decimales.")
    return int(texto)


def pedir_entero(mensaje):
    return pedir_con_validacion(mensaje, entero_positivo)


def pedir_numero(mensaje, campo, opcional=False, **limites):
    def revisar(texto):
        if opcional and not texto.strip():
            return None
        return validar_numero(texto.strip().replace(",", "."), campo, **limites)
    return pedir_con_validacion(mensaje, revisar)


def pedir_fecha(mensaje, opcional=False):
    def revisar(texto):
        texto = texto.strip()
        if opcional and not texto:
            return None
        try:
            if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", texto):
                raise ValueError
            return date.fromisoformat(texto)
        except ValueError:
            raise ValueError("Ingrese una fecha real con formato AAAA-MM-DD, por ejemplo 2026-03-15.") from None
    return pedir_con_validacion(mensaje, revisar)


def pedir_nombre_empleado(mensaje="Nombre: ", opcional=False):
    def revisar(texto):
        if opcional and not texto.strip():
            return ""
        return Empleado.validar_nombre(texto)
    return pedir_con_validacion(mensaje, revisar)


def pedir_correo_nuevo(id_actual=None):
    def revisar(texto):
        correo = Empleado.validar_correo(texto)
        existente = EmpleadoDAO.buscar_por_correo(correo)
        if existente is not None and existente.id_empleado != id_actual:
            raise ValueError("Ese correo ya está registrado. Ingrese otro.")
        return correo
    return pedir_con_validacion("Correo: ", revisar)


def pedir_identificacion_nueva(id_actual=None):
    def revisar(texto):
        identificacion = validar_identificacion(texto)
        existente = EmpleadoDAO.buscar_por_identificacion(identificacion)
        if existente is not None and existente.id_empleado != id_actual:
            raise ValueError("Esa identificación ya pertenece a otro empleado.")
        return identificacion
    return pedir_con_validacion("Identificación del empleado (por ejemplo EMP0001): ", revisar)


def pedir_nombre_usuario_nuevo(id_actual=None):
    def revisar(texto):
        nombre = validar_nombre_usuario(texto)
        existente = UsuarioDAO.buscar_por_nombre(nombre)
        if existente is not None and existente.id_usuario != id_actual:
            raise ValueError("Ese nombre de usuario ya está ocupado.")
        return nombre
    return pedir_con_validacion("Nombre de usuario: ", revisar)


def pedir_contrasena():
    return pedir_con_validacion("Contraseña (8 o más caracteres, letras y números): ", validar_contrasena, secreto=True)


def pedir_objeto(mensaje, buscar, nombre):
    while True:
        objeto = buscar(pedir_entero(mensaje))
        if objeto is not None:
            return objeto
        print(f"No encontramos {nombre} con ese id. Intente nuevamente o cancele con Ctrl+C.")


def confirmar(mensaje):
    def revisar(texto):
        respuesta = texto.strip().lower()
        if respuesta not in ("s", "n"):
            raise ValueError("Responda s para confirmar o n para cancelar.")
        return respuesta == "s"
    return pedir_con_validacion(f"{mensaje} (s/n): ", revisar)


def ejecutar(accion):
    try:
        accion()
    except (TypeError, ValueError) as error:
        print(f"Revise el dato: {error}")
    except (DAOError, ConexionError) as error:
        print(f"No se guardaron los cambios: {error}")
    except OSError:
        print("No se pudo guardar el archivo. Revise el nombre y los permisos.")
    except (KeyboardInterrupt, EOFError):
        print("\nOperación cancelada.")
    except Exception:
        logging.getLogger(__name__).exception("Error inesperado en el menú")
        print("Ocurrió un problema inesperado. El detalle quedó en ecotech.log.")


def mostrar_lista(titulo, elementos):
    print(f"\n--- {titulo} ---")
    if not elementos:
        print("No hay registros todavía.")
    for elemento in elementos:
        print(elemento)


def informar(resultado, ok, no):
    print(ok if resultado else no)


def acceso_vigente(usuario, modulo):
    actual = UsuarioDAO.buscar_por_id(usuario.id_usuario)
    if actual is None or not actual.puede_acceder(modulo):
        print("La cuenta está desactivada o no tiene permiso para esta opción.")
        return False
    return True


def submenu(titulo, opciones, usuario, modulo):
    while True:
        if not acceso_vigente(usuario, modulo):
            return
        print(f"\n=== {titulo} ===")
        for clave, (nombre, _) in opciones.items():
            print(f"{clave}. {nombre}")
        print("0. Volver")
        opcion = input("Seleccione una opción: ").strip()
        if opcion == "0":
            return
        if opcion in opciones:
            if not acceso_vigente(usuario, modulo):
                return
            ejecutar(opciones[opcion][1])
        else:
            print("La opción no existe. Elija uno de los números del menú.")


def ruta_exportacion(nombre, extension):
    # El usuario elige un nombre, pero no puede cambiar la carpeta de los informes.
    limpio = re.sub(r"[^\w.\-]", "_", Path(nombre).name)
    if not limpio.strip("."):
        raise ValueError("Ingrese un nombre de archivo válido.")
    if extension not in (".pdf", ".xlsx"):
        raise ValueError("Elija PDF o Excel.")
    if not limpio.lower().endswith(extension):
        limpio += extension
    return RAIZ_PROYECTO / "reportes" / limpio
