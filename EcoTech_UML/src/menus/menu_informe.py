from src.persistencia import (
    DepartamentoDAO, EmpleadoDAO, InformeDAO, ProyectoDAO, RegistroTiempoDAO,
)
from .comunes import (
    confirmar, informar, mostrar_lista, pedir_objeto, pedir_texto, ruta_exportacion, submenu,
)


def preparar_informe(admin, tipo):
    return admin.generar_informe(tipo, EmpleadoDAO.listar(), DepartamentoDAO.listar(),
                                ProyectoDAO.listar(), RegistroTiempoDAO.listar())


def generar_informe(admin):
    informe = preparar_informe(admin, pedir_texto("Título del informe: ", "El tipo de informe"))
    InformeDAO.insertar(informe)
    print(f"Informe guardado. Id: {informe.id_informe}.")
    print(informe._texto_legible())


def seleccionar_informe():
    return pedir_objeto("Id del informe: ", InformeDAO.buscar_por_id, "un informe")


def buscar_informe():
    print(seleccionar_informe()._texto_legible())


def actualizar_informe(admin):
    anterior = seleccionar_informe()
    if anterior.creado_por != admin.id_usuario:
        print("Solo el autor puede recalcular su informe. Puede generar uno nuevo con su cuenta.")
        return
    if not confirmar("¿Recalcular con los datos actuales? Se reemplazará el contenido guardado"):
        return
    tipo = pedir_texto("Nuevo título (Enter para mantener): ", "El tipo", opcional=True) or anterior.tipo
    informe = preparar_informe(admin, tipo)
    informe.id_informe = anterior.id_informe
    informar(InformeDAO.actualizar(informe), "Informe recalculado; conserva su autor.", "El informe ya no existe.")


def exportar_informe(extension):
    informe = seleccionar_informe()
    ruta = ruta_exportacion(pedir_texto("Nombre del archivo: ", "El nombre del archivo", 80), extension)
    if ruta.exists() and not confirmar("El archivo ya existe. ¿Reemplazarlo?"):
        return
    if extension == ".pdf":
        informe.exportar_pdf(str(ruta))
    else:
        informe.exportar_excel(str(ruta))
    print(f"Informe exportado en {ruta}.")


def eliminar_informe():
    informe = seleccionar_informe()
    if confirmar(f"¿Eliminar el informe {informe.id_informe}?"):
        informar(InformeDAO.eliminar(informe.id_informe), "Informe eliminado.", "El informe ya no existe.")


def menu_informe(admin):
    submenu("Informes", {
        "1": ("Generar informe general", lambda: generar_informe(admin)),
        "2": ("Listar", lambda: mostrar_lista("Informes", InformeDAO.listar())),
        "3": ("Buscar y leer", buscar_informe),
        "4": ("Recalcular un informe propio", lambda: actualizar_informe(admin)),
        "5": ("Exportar a PDF", lambda: exportar_informe(".pdf")),
        "6": ("Exportar a Excel", lambda: exportar_informe(".xlsx")),
        "7": ("Eliminar", eliminar_informe),
    }, admin, "informes")
