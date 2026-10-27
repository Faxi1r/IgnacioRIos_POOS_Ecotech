from src.dependencia import Departamento
from .conexion import marcador_sql
from .dao_util import DAOError, exigir_guardado, exigir_nuevo, sesion_bd
from .empleado_dao import EmpleadoDAO

_SELECT = "SELECT id_departamento, nombre, id_gerente FROM departamento"


class DepartamentoDAO:
    @staticmethod
    def _comprobar_empleado(cursor, id_empleado, id_departamento):
        cursor.execute(f"SELECT id_departamento FROM empleado WHERE id_empleado = {marcador_sql()}", (id_empleado,))
        fila = cursor.fetchone()
        if fila is None:
            raise DAOError("No encontramos al empleado indicado.")
        if fila[0] is not None and fila[0] != id_departamento:
            raise DAOError("El empleado ya tiene departamento. Use la opción de reasignar.")

    @staticmethod
    def _armar(fila):
        empleados = EmpleadoDAO.listar_por_departamento(fila[0])
        gerente = next((e for e in empleados if e.id_empleado == fila[2]), None)
        if gerente is None:
            raise DAOError("El gerente no pertenece al departamento. Revise la base de datos.")
        return Departamento(fila[0], fila[1], gerente, empleados)

    @staticmethod
    def insertar(departamento):
        exigir_nuevo(departamento.id_departamento, "El departamento")
        departamento.validar_datos()
        p = marcador_sql()
        with sesion_bd() as cursor:
            for empleado in departamento.empleados:
                exigir_guardado(empleado.id_empleado, "El empleado")
                DepartamentoDAO._comprobar_empleado(cursor, empleado.id_empleado, None)
            cursor.execute(f"INSERT INTO departamento (nombre, id_gerente) VALUES ({p}, {p})",
                           (departamento.nombre, departamento.gerente.id_empleado))
            nuevo_id = cursor.lastrowid
            for empleado in departamento.empleados:
                cursor.execute(f"UPDATE empleado SET id_departamento = {p} WHERE id_empleado = {p}",
                               (nuevo_id, empleado.id_empleado))
        departamento.id_departamento = nuevo_id
        return departamento

    @staticmethod
    def buscar_por_id(id_departamento):
        with sesion_bd() as cursor:
            cursor.execute(f"{_SELECT} WHERE id_departamento = {marcador_sql()}", (id_departamento,))
            fila = cursor.fetchone()
        return DepartamentoDAO._armar(fila) if fila else None

    @staticmethod
    def buscar_por_nombre(nombre):
        with sesion_bd() as cursor:
            cursor.execute(f"{_SELECT} WHERE nombre = {marcador_sql()}", (nombre.strip(),))
            fila = cursor.fetchone()
        return DepartamentoDAO._armar(fila) if fila else None

    @staticmethod
    def listar():
        with sesion_bd() as cursor:
            cursor.execute(f"{_SELECT} ORDER BY id_departamento")
            filas = cursor.fetchall()
        return [DepartamentoDAO._armar(fila) for fila in filas]

    @staticmethod
    def actualizar(departamento):
        exigir_guardado(departamento.id_departamento, "El departamento")
        departamento.validar_datos()
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(f"SELECT 1 FROM departamento WHERE id_departamento = {p}", (departamento.id_departamento,))
            if cursor.fetchone() is None:
                return False
            gerente = departamento.gerente.id_empleado
            exigir_guardado(gerente, "El gerente")
            DepartamentoDAO._comprobar_empleado(cursor, gerente, departamento.id_departamento)
            cursor.execute(f"UPDATE empleado SET id_departamento = {p} WHERE id_empleado = {p}",
                           (departamento.id_departamento, gerente))
            cursor.execute(f"UPDATE departamento SET nombre = {p}, id_gerente = {p} WHERE id_departamento = {p}",
                           (departamento.nombre, gerente, departamento.id_departamento))
            return True

    @staticmethod
    def agregar_empleado(id_departamento, id_empleado):
        p = marcador_sql()
        with sesion_bd() as cursor:
            DepartamentoDAO._comprobar_empleado(cursor, id_empleado, id_departamento)
            cursor.execute(f"UPDATE empleado SET id_departamento = {p} WHERE id_empleado = {p}",
                           (id_departamento, id_empleado))
            return cursor.rowcount > 0

    @staticmethod
    def quitar_empleado(id_departamento, id_empleado):
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(f"SELECT 1 FROM departamento WHERE id_departamento = {p} AND id_gerente = {p}",
                           (id_departamento, id_empleado))
            if cursor.fetchone():
                raise DAOError("Designe a otro gerente antes de quitar al actual.")
            cursor.execute(f"UPDATE empleado SET id_departamento = NULL WHERE id_empleado = {p} AND id_departamento = {p}",
                           (id_empleado, id_departamento))
            return cursor.rowcount > 0

    @staticmethod
    def reasignar_empleado(id_empleado, id_destino):
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(f"SELECT id_departamento FROM empleado WHERE id_empleado = {p}", (id_empleado,))
            fila = cursor.fetchone()
            if fila is None:
                return False
            if fila[0] == id_destino:
                return True
            cursor.execute(f"SELECT 1 FROM departamento WHERE id_gerente = {p}", (id_empleado,))
            if cursor.fetchone():
                raise DAOError("Cambie al gerente del departamento de origen antes de reasignarlo.")
            cursor.execute(f"UPDATE empleado SET id_departamento = {p} WHERE id_empleado = {p}", (id_destino, id_empleado))
            return True

    @staticmethod
    def eliminar(id_departamento):
        with sesion_bd() as cursor:
            cursor.execute(f"DELETE FROM departamento WHERE id_departamento = {marcador_sql()}", (id_departamento,))
            return cursor.rowcount > 0
