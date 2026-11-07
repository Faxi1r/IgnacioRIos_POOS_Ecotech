"""Guarda y consulta el historial local de indicadores."""
from datetime import date, datetime

from src.dependencia.indicador import Indicador
from src.persistencia.conexion import marcador_sql, obtener_motor
from src.persistencia.dao_util import sesion_bd


class IndicadorDAO:
    """Operaciones de base de datos para el historial de indicadores."""

    @staticmethod
    def guardar(indicador):
        """Guarda un indicador o actualiza su valor si ya existe esa fecha."""
        IndicadorDAO.guardar_varios([indicador])

    @staticmethod
    def guardar_varios(indicadores):
        """Guarda una serie completa dentro de una sola transacción."""
        indicadores = list(indicadores)
        if not indicadores:
            raise ValueError("No hay indicadores para guardar.")
        if any(not isinstance(item, Indicador) for item in indicadores):
            raise TypeError("Todos los elementos deben ser objetos Indicador.")

        p = marcador_sql()
        if obtener_motor() == "mysql":
            sql = (
                "INSERT INTO indicador_api "
                "(fuente, codigo, fecha, valor, unidad, verificado_en) "
                f"VALUES ({p}, {p}, {p}, {p}, {p}, {p}) "
                "ON DUPLICATE KEY UPDATE valor = VALUES(valor), "
                "unidad = VALUES(unidad), verificado_en = VALUES(verificado_en)"
            )
        else:
            sql = (
                "INSERT INTO indicador_api "
                "(fuente, codigo, fecha, valor, unidad, verificado_en) "
                f"VALUES ({p}, {p}, {p}, {p}, {p}, {p}) "
                "ON CONFLICT(fuente, codigo, fecha) DO UPDATE SET "
                "valor = excluded.valor, unidad = excluded.unidad, "
                "verificado_en = excluded.verificado_en"
            )

        with sesion_bd() as cursor:
            for indicador in indicadores:
                verificado = (indicador.verificado_en or datetime.now()).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                valores = (
                    indicador.fuente,
                    indicador.codigo,
                    indicador.fecha.isoformat(),
                    indicador.valor,
                    indicador.unidad,
                    verificado,
                )
                cursor.execute(sql, valores)

    @staticmethod
    def listar_historial(codigo, limite=20, fuente="open.er-api.com", unidad="Pesos"):
        """Devuelve los registros más recientes de un indicador."""
        if codigo not in ("dolar", "euro"):
            raise ValueError("Indicador no válido.")
        if type(limite) is not int or not 1 <= limite <= 100:
            raise ValueError("El límite debe estar entre 1 y 100.")

        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(
                "SELECT codigo, fecha, valor, unidad, fuente, verificado_en "
                f"FROM indicador_api WHERE codigo = {p} AND fuente = {p} AND unidad = {p} "
                f"ORDER BY fecha DESC LIMIT {p}",
                (codigo, fuente, unidad, limite),
            )
            filas = cursor.fetchall()

        historial = []
        for fila in filas:
            fecha = fila[1]
            if isinstance(fecha, datetime):
                fecha = fecha.date()
            elif not isinstance(fecha, date):
                fecha = date.fromisoformat(str(fecha).split(" ")[0])

            verificado = fila[5]
            if isinstance(verificado, str):
                try:
                    verificado = datetime.fromisoformat(verificado)
                except ValueError:
                    verificado = None

            historial.append(
                Indicador(
                    codigo=fila[0],
                    fecha=fecha,
                    valor=float(fila[2]),
                    unidad=fila[3],
                    fuente=fila[4],
                    verificado_en=verificado,
                )
            )
        return historial
