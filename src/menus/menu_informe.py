from src.servicios import gestion_informes
from src.servicios.permisos import exigir_admin
from .comunes import (
    confirmar,
    informar,
    mostrar_lista,
    pedir_objeto,
    pedir_texto,
    ruta_exportacion,
    submenu,
)


def generar_informe(sesion):
    exigir_admin(sesion)
    informe = gestion_informes.generar(
        sesion, pedir_texto("Título del informe: ", "El tipo de informe")
    )
    print(f"Informe guardado. Id: {informe.id_informe}.")
    print(informe._texto_legible())


def seleccionar_informe(sesion):
    exigir_admin(sesion)
    return pedir_objeto(
        "Id del informe: ",
        lambda identificador: gestion_informes.buscar_por_id(sesion, identificador),
        "un informe",
    )


def buscar_informe(sesion):
    print(seleccionar_informe(sesion)._texto_legible())


def actualizar_informe(sesion):
    exigir_admin(sesion)
    anterior = seleccionar_informe(sesion)
    if anterior.creado_por != sesion["id"]:
        print("Solo el autor puede recalcular su informe. Puede generar uno nuevo con su cuenta.")
        return
    if confirmar("¿Recalcular con los datos actuales? Se reemplazará el contenido guardado"):
        tipo = (
            pedir_texto("Nuevo título (Enter para mantener): ", "El tipo", opcional=True)
            or anterior.tipo
        )
        informar(
            gestion_informes.recalcular(sesion, anterior.id_informe, tipo),
            "Informe recalculado; conserva su autor.",
            "El informe ya no existe.",
        )


def exportar_informe(sesion, extension):
    informe = seleccionar_informe(sesion)
    ruta = ruta_exportacion(
        pedir_texto("Nombre del archivo: ", "El nombre del archivo", 80), extension
    )
    if ruta.exists() and not confirmar("El archivo ya existe. ¿Reemplazarlo?"):
        return
    gestion_informes.exportar(sesion, informe.id_informe, ruta, extension)
    print(f"Informe exportado en {ruta}.")


def eliminar_informe(sesion):
    informe = seleccionar_informe(sesion)
    if confirmar(f"¿Eliminar el informe {informe.id_informe}?"):
        informar(
            gestion_informes.eliminar(sesion, informe.id_informe),
            "Informe eliminado.",
            "El informe ya no existe.",
        )


def menu_informe(sesion):
    submenu(
        "Informes",
        {
            "1": ("Generar informe general", lambda: generar_informe(sesion)),
            "2": ("Listar", lambda: mostrar_lista("Informes", gestion_informes.listar(sesion))),
            "3": ("Buscar y leer", lambda: buscar_informe(sesion)),
            "4": ("Recalcular un informe propio", lambda: actualizar_informe(sesion)),
            "5": ("Exportar a PDF", lambda: exportar_informe(sesion, ".pdf")),
            "6": ("Exportar a Excel", lambda: exportar_informe(sesion, ".xlsx")),
            "7": ("Eliminar", lambda: eliminar_informe(sesion)),
        },
        sesion,
        "informes",
    )
