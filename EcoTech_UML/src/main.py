"""Inicio del programa. Los menús piden datos y los DAO se encargan de guardarlos."""
import argparse
import getpass
import logging
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.menus.menu_departamento import menu_departamento
from src.menus.menu_empleado import menu_empleado
from src.menus.menu_informe import menu_informe
from src.menus.menu_proyecto import menu_proyecto
from src.menus.menu_registro import menu_registro
from src.menus.menu_usuario import menu_usuario
from src.menus.menu_usuario import crear_usuario
from src.menus.menu_personal import menu_personal
from src.menus.menu_indicadores import consultar_dolar
from src.menus.comunes import acceso_vigente
from src.dependencia import Administrador
from src.persistencia import ConexionError, DAOError, UsuarioDAO, crear_tablas
from src.persistencia.conexion import RAIZ_PROYECTO, describir_conexion


def iniciar_sesion():
    for _ in range(3):
        nombre = input("Nombre de usuario: ").strip()
        usuario = UsuarioDAO.autenticar(nombre, getpass.getpass("Contraseña: "))
        if usuario:
            return usuario
        print("Usuario o contraseña incorrectos.")
    print("No se pudo iniciar sesión después de tres intentos.")
    return None


def menu_principal(usuario):
    if not isinstance(usuario, Administrador):
        menu_personal(usuario)
        return
    opciones = {
        "1": ("Empleados", lambda: menu_empleado(usuario)),
        "2": ("Departamentos", lambda: menu_departamento(usuario)),
        "3": ("Proyectos", lambda: menu_proyecto(usuario)),
        "4": ("Registro de horas", lambda: menu_registro(usuario)),
        "5": ("Usuarios y administradores", lambda: menu_usuario(usuario)),
        "6": ("Informes", lambda: menu_informe(usuario)),
        "7": ("Consultar dólar observado", consultar_dolar),
    }
    while True:
        if not acceso_vigente(usuario, "mi_cuenta"):
            return
        print("\n===== ECOTECH =====")
        for numero, (nombre, _) in opciones.items():
            print(f"{numero}. {nombre}")
        print("0. Salir")
        opcion = input("Seleccione una opción: ").strip()
        if opcion == "0":
            return
        if opcion in opciones:
            opciones[opcion][1]()
        else:
            print("La opción no existe. Seleccione un número del menú.")


def main():
    parser = argparse.ArgumentParser(description="Sistema EcoTech por consola")
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--comprobar-conexion", action="store_true", help="Comprobar qué motor responde")
    modo.add_argument("--demo", action="store_true", help="Probar CRUD y relaciones con datos ficticios")
    modo.add_argument("--semilla", action="store_true", help="Cargar datos ficticios sin duplicarlos")
    modo.add_argument("--crear-admin", action="store_true", help="Crear el primer administrador de una base nueva")
    argumentos = parser.parse_args()
    logging.basicConfig(filename=str(RAIZ_PROYECTO / "ecotech.log"), level=logging.WARNING,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        print(describir_conexion())
        if argumentos.comprobar_conexion:
            return 0
        crear_tablas()
        if argumentos.demo:
            from src.demostracion import ejecutar_demostracion
            ejecutar_demostracion()
        elif argumentos.semilla:
            from src.persistencia.semilla_bd import cargar_semilla
            cargar_semilla()
        elif argumentos.crear_admin:
            if UsuarioDAO.hay_administradores():
                print("Ya existe un administrador. Inicie sesión para crear otras cuentas.")
                return 1
            crear_usuario(es_admin=True)
        else:
            if not UsuarioDAO.hay_administradores():
                print("Primero ejecute python -m src.main --crear-admin, o use --semilla para practicar.")
                return 1
            print("En un formulario puede usar Ctrl+C para cancelar la operación.")
            usuario = iniciar_sesion()
            if usuario is None:
                return 1
            print(f"Bienvenido, {usuario.nombre_usuario}.")
            menu_principal(usuario)
    except (ConexionError, DAOError, ValueError) as error:
        print(f"No fue posible continuar: {error}")
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nHasta luego.")
        return 0
    except Exception:
        logging.getLogger(__name__).exception("Error al ejecutar el programa")
        print("Ocurrió un problema inesperado. Revise ecotech.log.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
