"""Inicio del programa. Los servicios revisan los permisos antes de usar los DAO."""

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
from src.menus.menu_empleado import pedir_datos_empleado
from src.menus.comunes import pedir_nombre_usuario_nuevo, pedir_contrasena, ejecutar
from src.menus.menu_personal import menu_personal, ver_mis_datos, ver_mis_horas
from src.menus.menu_indicadores import menu_indicadores
from src.menus.comunes import acceso_vigente
from src.servicios.autenticacion import autenticar, cerrar_sesion
from src.servicios.preparacion import crear_admin_inicial
from src.persistencia import ConexionError, DAOError, UsuarioDAO, crear_tablas
from src.persistencia.conexion import RAIZ_PROYECTO, describir_conexion


def iniciar_sesion():
    for _ in range(3):
        nombre = input("Nombre de usuario: ").strip()
        usuario = autenticar(nombre, getpass.getpass("Contraseña: "))
        if usuario:
            return usuario
        print("Usuario o contraseña incorrectos.")
    print("No se pudo iniciar sesión después de tres intentos.")
    return None


def menu_principal(sesion):
    opciones = {
        "1": ("Mi ficha", lambda: ver_mis_datos(sesion)),
        "2": ("Mis registros", lambda: ver_mis_horas(sesion)),
        "3": ("Indicadores financieros", lambda: menu_indicadores(sesion)),
        "11": ("Editar mis datos y otras opciones personales", lambda: menu_personal(sesion)),
    }
    if sesion["rol"] == "admin":
        opciones.update(
            {
                "4": ("Administrar empleados", lambda: menu_empleado(sesion)),
                "5": ("Departamentos", lambda: menu_departamento(sesion)),
                "6": ("Proyectos", lambda: menu_proyecto(sesion)),
                "7": ("Registros de todo el sistema", lambda: menu_registro(sesion)),
                "8": ("Cuentas de usuario", lambda: menu_usuario(sesion)),
                "10": ("Informes", lambda: menu_informe(sesion)),
            }
        )
    while True:
        if not acceso_vigente(sesion, "mi_cuenta"):
            cerrar_sesion(sesion)
            return "cerrar"
        print("\n===== ECOTECH =====")
        for numero in sorted(opciones, key=int):
            print(f"{numero}. {opciones[numero][0]}")
        print("9. Cerrar sesión")
        print("0. Salir")
        opcion = input("Seleccione una opción: ").strip()
        if opcion in ("0", "9"):
            cerrar_sesion(sesion)
            return "salir" if opcion == "0" else "cerrar"
        if opcion in opciones:
            if acceso_vigente(sesion, "mi_cuenta"):
                ejecutar(opciones[opcion][1])
        else:
            print("La opción no está disponible para esta cuenta.")


def main():
    parser = argparse.ArgumentParser(description="Sistema EcoTech por consola")
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument(
        "--comprobar-conexion", action="store_true", help="Comprobar qué motor responde"
    )
    modo.add_argument(
        "--demo", action="store_true", help="Probar CRUD y relaciones con datos ficticios"
    )
    modo.add_argument(
        "--semilla", action="store_true", help="Cargar datos ficticios sin duplicarlos"
    )
    modo.add_argument(
        "--crear-admin", action="store_true", help="Crear el primer administrador de una base nueva"
    )
    argumentos = parser.parse_args()
    logging.basicConfig(
        filename=str(RAIZ_PROYECTO / "ecotech.log"),
        level=logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
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
            print("Prepare la cuenta y la ficha del primer administrador.")
            nombre = pedir_nombre_usuario_nuevo()
            contrasena = pedir_contrasena()
            empleado = pedir_datos_empleado()
            crear_admin_inicial(nombre, contrasena, empleado)
            print("Primer administrador creado y vinculado a su empleado.")
        else:
            if not UsuarioDAO.hay_administradores():
                print(
                    "Primero ejecute python -m src.main --crear-admin, o use --semilla para practicar."
                )
                return 1
            print("En un formulario puede usar Ctrl+C para cancelar la operación.")
            while True:
                sesion = iniciar_sesion()
                if sesion is None:
                    return 1
                print(f"Bienvenido, {sesion['nombre_usuario']}.")
                if menu_principal(sesion) == "salir":
                    break
                print("Sesión cerrada. Puede ingresar con otra cuenta.")
    except (ConexionError, DAOError, ValueError, PermissionError) as error:
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
