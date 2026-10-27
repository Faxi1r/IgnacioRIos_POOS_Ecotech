from src.dependencia import Administrador, Usuario
from .conexion import marcador_sql
from .dao_util import DAOError, exigir_guardado, exigir_nuevo, sesion_bd

_SELECT = ("SELECT u.id_usuario, u.nombre_usuario, u.contrasena_hash, u.activo, a.id_usuario "
           "FROM usuario u LEFT JOIN administrador a ON a.id_usuario = u.id_usuario")


class UsuarioDAO:
    @staticmethod
    def _armar(fila):
        clase = Administrador if fila[4] is not None else Usuario
        return clase(fila[0], fila[1], fila[2], bool(fila[3]))

    @staticmethod
    def insertar(usuario):
        if not isinstance(usuario, Usuario):
            raise ValueError("Aquí se guardan cuentas de usuario.")
        exigir_nuevo(usuario.id_usuario, "El usuario")
        if not usuario.contrasena_hash:
            raise DAOError("Establezca una contraseña antes de guardar la cuenta.")
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(f"INSERT INTO usuario (nombre_usuario, contrasena_hash, activo) VALUES ({p}, {p}, {p})",
                           (usuario.nombre_usuario, usuario.contrasena_hash, int(usuario.activo)))
            nuevo_id = cursor.lastrowid
            if isinstance(usuario, Administrador):
                cursor.execute(f"INSERT INTO administrador (id_usuario) VALUES ({p})", (nuevo_id,))
        usuario.id_usuario = nuevo_id
        return usuario

    @staticmethod
    def buscar_por_id(id_usuario):
        with sesion_bd() as cursor:
            cursor.execute(f"{_SELECT} WHERE u.id_usuario = {marcador_sql()}", (id_usuario,))
            fila = cursor.fetchone()
        return UsuarioDAO._armar(fila) if fila else None

    @staticmethod
    def buscar_por_nombre(nombre_usuario):
        with sesion_bd() as cursor:
            cursor.execute(f"{_SELECT} WHERE u.nombre_usuario = {marcador_sql()}",
                           (nombre_usuario.strip().lower(),))
            fila = cursor.fetchone()
        return UsuarioDAO._armar(fila) if fila else None

    @staticmethod
    def autenticar(nombre_usuario, contrasena):
        if not isinstance(nombre_usuario, str):
            return None
        usuario = UsuarioDAO.buscar_por_nombre(nombre_usuario)
        return usuario if usuario and usuario.autenticar(contrasena) else None

    @staticmethod
    def listar():
        with sesion_bd() as cursor:
            cursor.execute(f"{_SELECT} ORDER BY u.id_usuario")
            filas = cursor.fetchall()
        return [UsuarioDAO._armar(fila) for fila in filas]

    @staticmethod
    def hay_administradores():
        with sesion_bd() as cursor:
            cursor.execute("SELECT COUNT(*) FROM administrador")
            return cursor.fetchone()[0] > 0

    @staticmethod
    def actualizar(usuario):
        exigir_guardado(usuario.id_usuario, "El usuario")
        p = marcador_sql()
        with sesion_bd() as cursor:
            cursor.execute(f"SELECT u.activo, a.id_usuario FROM usuario u LEFT JOIN administrador a "
                           f"ON a.id_usuario = u.id_usuario WHERE u.id_usuario = {p}", (usuario.id_usuario,))
            anterior = cursor.fetchone()
            if anterior is None:
                return False
            if bool(anterior[1] is not None) != isinstance(usuario, Administrador):
                raise DAOError("El tipo de una cuenta no se cambia desde actualizar.")
            if anterior[0] and not usuario.activo and anterior[1] is not None:
                cursor.execute("SELECT COUNT(*) FROM administrador a JOIN usuario u ON u.id_usuario = a.id_usuario "
                               "WHERE u.activo = 1")
                if cursor.fetchone()[0] <= 1:
                    raise DAOError("Debe quedar al menos un administrador activo.")
            cursor.execute(f"UPDATE usuario SET nombre_usuario = {p}, contrasena_hash = {p}, activo = {p} "
                           f"WHERE id_usuario = {p}",
                           (usuario.nombre_usuario, usuario.contrasena_hash, int(usuario.activo), usuario.id_usuario))
            return cursor.rowcount > 0
