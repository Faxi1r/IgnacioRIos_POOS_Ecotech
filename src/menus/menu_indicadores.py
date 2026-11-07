"""Menú simple para consultar indicadores y revisar su historial."""
from src.indicadores import ErrorAPI, INDICADORES
from src.persistencia import ConexionError, DAOError
from src.servicios.indicadores import consultar_historial, consultar_indicador, convertir_monto, validar_monto
from src.servicios.permisos import exigir_sesion

OPCIONES_INDICADOR = {
    "1": "dolar",
    "2": "euro",
}


def _nombre_indicador(codigo):
    return INDICADORES[codigo]


def _mostrar_indicador(indicador):
    print(f"\n{_nombre_indicador(indicador.codigo)}")
    print(f"Fecha del valor: {indicador.fecha.isoformat()}")
    print(f"Valor: ${indicador.valor:,.2f} CLP por unidad")
    print(f"Fuente: {indicador.fuente}")
    verificado = indicador.verificado_en
    print(f"Última verificación (hora local): {verificado.isoformat(sep=' ') if verificado else 'No registrada'}")


def _convertir_monto(sesion, indicador, origen):
    respuesta = input("¿Desea convertir un monto en CLP? (s/n): ").strip().lower()
    if respuesta != "s":
        return
    while True:
        texto = input("Monto en CLP (sin separadores de miles): ").strip()
        try:
            monto = validar_monto(texto)
            resultado = convertir_monto(sesion, texto, indicador)
            break
        except ValueError as error:
            print(error)
    print(f"{monto} CLP equivalen a {resultado} {indicador.codigo.upper()}.")
    print("Estimación de referencia; no realiza pagos ni incluye comisiones.")
    if origen == "BD":
        print("Atención: se utilizó una tasa guardada. Compruebe la fecha antes de usar el resultado.")


def _consultar(sesion, codigo):
    try:
        indicador, origen, mensaje = consultar_indicador(sesion, codigo)
        print(mensaje)
        if indicador is None:
            return
        _mostrar_indicador(indicador)
        print(f"Origen de esta lectura: {origen}")
        _convertir_monto(sesion, indicador, origen)
    except ErrorAPI as error:
        print(f"No se pudo consultar la API: {error}")
    except (ValueError, TypeError) as error:
        print(f"No se pudieron validar los datos recibidos: {error}")
    except (DAOError, ConexionError) as error:
        print(f"No se pudo completar la operación en la base de datos: {error}")
    except PermissionError as error:
        print(error)


def _mostrar_historial(sesion):
    print("\n¿Qué historial desea consultar?")
    print("1. Dólar")
    print("2. Euro")
    print("0. Volver")
    opcion = input("Seleccione: ").strip()
    if opcion == "0":
        return

    codigo = OPCIONES_INDICADOR.get(opcion)
    if codigo is None:
        print("Seleccione una opción válida.")
        return

    try:
        historial = consultar_historial(sesion, codigo)
        print(f"\n--- Historial de {_nombre_indicador(codigo)} | Origen: BD ---")
        if not historial:
            print("Todavía no hay consultas guardadas para este indicador.")
            return
        for indicador in historial:
            _mostrar_indicador(indicador)
    except (DAOError, ConexionError, PermissionError, ValueError) as error:
        print(f"No se pudo consultar el historial: {error}")


def menu_indicadores(sesion):
    """Muestra el menú de indicadores mientras la sesión siga vigente."""
    while True:
        try:
            exigir_sesion(sesion)
        except PermissionError as error:
            print(error)
            return

        print("\n--- INDICADORES FINANCIEROS ---")
        print("1. Consultar dólar (USD)")
        print("2. Consultar euro (EUR)")
        print("3. Ver historial guardado")
        print("0. Volver al menú principal")
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "0":
            return
        if opcion in OPCIONES_INDICADOR:
            _consultar(sesion, OPCIONES_INDICADOR[opcion])
        elif opcion == "3":
            _mostrar_historial(sesion)
        else:
            print("La opción no existe. Elija uno de los números del menú.")


def consultar_dolar(sesion):
    """Consulta directa del dólar, disponible para mantener la función anterior."""
    _consultar(sesion, "dolar")
