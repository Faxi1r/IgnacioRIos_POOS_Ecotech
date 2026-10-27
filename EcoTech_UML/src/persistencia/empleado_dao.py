import json
from datetime import date

from src.dependencia import Empleado, Seguridad
from src.dependencia.validaciones import validar_identificacion
from .conexion import marcador_sql
from .dao_util import DAOError, exigir_guardado, exigir_nuevo, sesion_bd
from .usuario_dao import UsuarioDAO

_SELECT = "SELECT id_empleado, datos_cifrados, id_departamento, id_usuario FROM empleado"


class EmpleadoDAO:
    @staticmethod
    def _armar(fila, cargar_departamento=True):
        datos = json.loads(Seguridad().descifrar(fila[1]))
        usuario = UsuarioDAO.buscar_por_id(fila[3]) if fila[3] is not None else None
        empleado = Empleado(fila[0], datos["identificacion"], datos["nombre"], datos["correo"],
                            datos["salario"], datos["direccion"], datos["telefono"],
                            date.fromisoformat(datos["fecha_inicio_contrato"]), usuario)
        empleado._id_departamento = fila[2]
        from .registro_tiempo_dao import RegistroTiempoDAO
        empleado._registros_tiempo = RegistroTiempoDAO.listar_por_empleado(empleado.id_empleado)
        if cargar_departamento and fila[2] is not None:
            from .departamento_dao import DepartamentoDAO
            empleado._departamento = DepartamentoDAO.buscar_por_id(fila[2])
        return empleado

    @staticmethod
    def insertar(empleado):
        exigir_nuevo(empleado.id_empleado, "El empleado")
        empleado.validar_datos()
        if empleado.departamento is not None:
            exigir_guardado(empleado.id_departamento, "El departamento")
        id_usuario = None
        if empleado.usuario is not None:
            exigir_guardado(empleado.usuario.id_usuario, "La cuenta")
            id_usuario = empleado.usuario.id_usuario
        seguridad = Seguridad()
        valores = (seguridad._indice_busqueda("identificacion", empleado.identificacion),
                   seguridad._indice_busqueda("correo", empleado.correo), empleado._cifrar_datos(),
                   empleado.id_departamento, id_usuario)
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute("INSERT INTO empleado (identificacion_indice, correo_indice, datos_cifrados, "
                           f"id_departamento, id_usuario) VALUES ({p}, {p}, {p}, {p}, {p})", valores)
            nuevo_id = cursor.lastrowid
        empleado.id_empleado = nuevo_id
        return empleado

    @staticmethod
    def _buscar(campo, valor):
        # Solo los métodos de esta clase eligen la columna; el valor lleva un parámetro.
        with sesion_bd() as cursor:
            cursor.execute(f"{_SELECT} WHERE {campo} = {marcador_sql()}", (valor,))
            fila = cursor.fetchone()
        return EmpleadoDAO._armar(fila) if fila else None

    @staticmethod
    def buscar_por_id(id_empleado):
        return EmpleadoDAO._buscar("id_empleado", id_empleado)

    @staticmethod
    def buscar_por_identificacion(identificacion):
        indice = Seguridad()._indice_busqueda("identificacion", validar_identificacion(identificacion))
        return EmpleadoDAO._buscar("identificacion_indice", indice)

    @staticmethod
    def buscar_por_correo(correo):
        indice = Seguridad()._indice_busqueda("correo", Empleado.validar_correo(correo))
        return EmpleadoDAO._buscar("correo_indice", indice)

    @staticmethod
    def buscar_por_usuario(id_usuario):
        return EmpleadoDAO._buscar("id_usuario", id_usuario)

    @staticmethod
    def listar():
        with sesion_bd() as cursor:
            cursor.execute(f"{_SELECT} ORDER BY id_empleado")
            filas = cursor.fetchall()
        return [EmpleadoDAO._armar(fila) for fila in filas]

    @staticmethod
    def listar_por_departamento(id_departamento):
        with sesion_bd() as cursor:
            cursor.execute(f"{_SELECT} WHERE id_departamento = {marcador_sql()} ORDER BY id_empleado",
                           (id_departamento,))
            filas = cursor.fetchall()
        # DepartamentoDAO completa esta relación sin volver a llamarse a sí mismo.
        return [EmpleadoDAO._armar(fila, cargar_departamento=False) for fila in filas]

    @staticmethod
    def listar_por_proyecto(id_proyecto):
        with sesion_bd() as cursor:
            cursor.execute(f"{_SELECT} WHERE id_empleado IN "
                           f"(SELECT id_empleado FROM proyecto_empleado WHERE id_proyecto = {marcador_sql()}) "
                           "ORDER BY id_empleado", (id_proyecto,))
            filas = cursor.fetchall()
        return [EmpleadoDAO._armar(fila) for fila in filas]

    @staticmethod
    def actualizar(empleado):
        exigir_guardado(empleado.id_empleado, "El empleado")
        empleado.validar_datos()
        seguridad = Seguridad()
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(f"UPDATE empleado SET identificacion_indice = {p}, correo_indice = {p}, "
                           f"datos_cifrados = {p} WHERE id_empleado = {p}",
                           (seguridad._indice_busqueda("identificacion", empleado.identificacion),
                            seguridad._indice_busqueda("correo", empleado.correo), empleado._cifrar_datos(),
                            empleado.id_empleado))
            return cursor.rowcount > 0

    @staticmethod
    def vincular_cuenta(id_empleado, id_usuario):
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(f"SELECT id_usuario FROM empleado WHERE id_empleado = {p}", (id_empleado,))
            fila = cursor.fetchone()
            if fila is None:
                return False
            if fila[0] is not None and fila[0] != id_usuario:
                raise DAOError("Desvincule primero la cuenta anterior.")
            cursor.execute(f"SELECT activo FROM usuario WHERE id_usuario = {p}", (id_usuario,))
            cuenta = cursor.fetchone()
            if cuenta is None or not cuenta[0]:
                raise DAOError("Seleccione una cuenta existente y activa.")
            cursor.execute(f"UPDATE empleado SET id_usuario = {p} WHERE id_empleado = {p}", (id_usuario, id_empleado))
            return True

    @staticmethod
    def desvincular_cuenta(id_empleado):
        with sesion_bd() as cursor:
            cursor.execute(f"UPDATE empleado SET id_usuario = NULL WHERE id_empleado = {marcador_sql()}", (id_empleado,))
            return cursor.rowcount > 0

    @staticmethod
    def eliminar(id_empleado):
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(f"SELECT 1 FROM departamento WHERE id_gerente = {p}", (id_empleado,))
            if cursor.fetchone():
                raise DAOError("El empleado es gerente. Designe a otra persona antes de eliminarlo.")
            cursor.execute(f"SELECT 1 FROM registro_tiempo WHERE id_empleado = {p}", (id_empleado,))
            if cursor.fetchone():
                raise DAOError("El empleado tiene horas guardadas. No se elimina para conservar su historial.")
            cursor.execute(f"DELETE FROM empleado WHERE id_empleado = {p}", (id_empleado,))
            return cursor.rowcount > 0
