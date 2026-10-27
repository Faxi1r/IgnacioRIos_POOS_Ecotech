"""Prepara las tablas del UML. La semilla se carga por separado."""
from src.dependencia.seguridad import Seguridad
from .conexion import obtener_motor, marcador_sql
from .dao_util import DAOError, sesion_bd

TABLAS_SQLITE = [
    """CREATE TABLE IF NOT EXISTS configuracion (
        clave TEXT PRIMARY KEY, valor TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS usuario (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_usuario TEXT NOT NULL UNIQUE, contrasena_hash TEXT NOT NULL,
        activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)))""",
    """CREATE TABLE IF NOT EXISTS administrador (
        id_usuario INTEGER PRIMARY KEY,
        FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE RESTRICT)""",
    """CREATE TABLE IF NOT EXISTS departamento (
        id_departamento INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE,
        id_gerente INTEGER NOT NULL UNIQUE,
        FOREIGN KEY (id_gerente) REFERENCES empleado(id_empleado) ON DELETE RESTRICT)""",
    """CREATE TABLE IF NOT EXISTS empleado (
        id_empleado INTEGER PRIMARY KEY AUTOINCREMENT,
        identificacion_indice TEXT NOT NULL UNIQUE, correo_indice TEXT NOT NULL UNIQUE,
        datos_cifrados TEXT NOT NULL, id_departamento INTEGER, id_usuario INTEGER UNIQUE,
        FOREIGN KEY (id_departamento) REFERENCES departamento(id_departamento) ON DELETE SET NULL,
        FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE RESTRICT)""",
    """CREATE TABLE IF NOT EXISTS proyecto (
        id_proyecto INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE,
        descripcion TEXT NOT NULL, fecha_inicio TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS proyecto_empleado (
        id_proyecto INTEGER NOT NULL, id_empleado INTEGER NOT NULL,
        PRIMARY KEY (id_proyecto, id_empleado),
        FOREIGN KEY (id_proyecto) REFERENCES proyecto(id_proyecto) ON DELETE CASCADE,
        FOREIGN KEY (id_empleado) REFERENCES empleado(id_empleado) ON DELETE CASCADE)""",
    """CREATE TABLE IF NOT EXISTS registro_tiempo (
        id_registro INTEGER PRIMARY KEY AUTOINCREMENT, id_empleado INTEGER NOT NULL,
        id_proyecto INTEGER NOT NULL, fecha TEXT NOT NULL,
        horas REAL NOT NULL CHECK (horas > 0 AND horas <= 24), descripcion_tareas TEXT NOT NULL,
        FOREIGN KEY (id_empleado) REFERENCES empleado(id_empleado) ON DELETE RESTRICT,
        FOREIGN KEY (id_proyecto) REFERENCES proyecto(id_proyecto) ON DELETE RESTRICT)""",
    """CREATE TABLE IF NOT EXISTS informe (
        id_informe INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT NOT NULL,
        fecha_generacion TEXT NOT NULL, contenido TEXT NOT NULL, creado_por INTEGER NOT NULL,
        FOREIGN KEY (creado_por) REFERENCES administrador(id_usuario) ON DELETE RESTRICT)""",
]

TABLAS_MYSQL = [
    """CREATE TABLE IF NOT EXISTS configuracion (
        clave VARCHAR(40) PRIMARY KEY, valor TEXT NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    """CREATE TABLE IF NOT EXISTS usuario (
        id_usuario INT PRIMARY KEY AUTO_INCREMENT, nombre_usuario VARCHAR(40) NOT NULL UNIQUE,
        contrasena_hash VARCHAR(255) NOT NULL, activo BOOLEAN NOT NULL DEFAULT TRUE,
        CHECK (activo IN (0, 1))) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    """CREATE TABLE IF NOT EXISTS administrador (
        id_usuario INT PRIMARY KEY,
        FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE RESTRICT)
        ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    """CREATE TABLE IF NOT EXISTS departamento (
        id_departamento INT PRIMARY KEY AUTO_INCREMENT, nombre VARCHAR(100) NOT NULL UNIQUE,
        id_gerente INT NOT NULL UNIQUE) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    """CREATE TABLE IF NOT EXISTS empleado (
        id_empleado INT PRIMARY KEY AUTO_INCREMENT,
        identificacion_indice CHAR(64) NOT NULL UNIQUE, correo_indice CHAR(64) NOT NULL UNIQUE,
        datos_cifrados TEXT NOT NULL, id_departamento INT NULL, id_usuario INT NULL UNIQUE,
        FOREIGN KEY (id_departamento) REFERENCES departamento(id_departamento) ON DELETE SET NULL,
        FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE RESTRICT)
        ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    """CREATE TABLE IF NOT EXISTS proyecto (
        id_proyecto INT PRIMARY KEY AUTO_INCREMENT, nombre VARCHAR(150) NOT NULL UNIQUE,
        descripcion VARCHAR(500) NOT NULL, fecha_inicio DATE NOT NULL)
        ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    """CREATE TABLE IF NOT EXISTS proyecto_empleado (
        id_proyecto INT NOT NULL, id_empleado INT NOT NULL,
        PRIMARY KEY (id_proyecto, id_empleado),
        FOREIGN KEY (id_proyecto) REFERENCES proyecto(id_proyecto) ON DELETE CASCADE,
        FOREIGN KEY (id_empleado) REFERENCES empleado(id_empleado) ON DELETE CASCADE)
        ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    """CREATE TABLE IF NOT EXISTS registro_tiempo (
        id_registro INT PRIMARY KEY AUTO_INCREMENT, id_empleado INT NOT NULL,
        id_proyecto INT NOT NULL, fecha DATE NOT NULL,
        horas DECIMAL(5,2) NOT NULL CHECK (horas > 0 AND horas <= 24),
        descripcion_tareas TEXT NOT NULL,
        FOREIGN KEY (id_empleado) REFERENCES empleado(id_empleado) ON DELETE RESTRICT,
        FOREIGN KEY (id_proyecto) REFERENCES proyecto(id_proyecto) ON DELETE RESTRICT)
        ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    """CREATE TABLE IF NOT EXISTS informe (
        id_informe INT PRIMARY KEY AUTO_INCREMENT, tipo VARCHAR(100) NOT NULL,
        fecha_generacion DATE NOT NULL, contenido LONGTEXT NOT NULL, creado_por INT NOT NULL,
        FOREIGN KEY (creado_por) REFERENCES administrador(id_usuario) ON DELETE RESTRICT)
        ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
]


def crear_tablas() -> None:
    es_mysql = obtener_motor() == "mysql"
    seguridad = Seguridad()
    with sesion_bd() as cursor:
        if es_mysql:
            cursor.execute("SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                           "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'usuario'")
            columnas = [fila[0] for fila in cursor.fetchall()]
        else:
            cursor.execute("PRAGMA table_info(usuario)")
            columnas = [fila[1] for fila in cursor.fetchall()]
        if columnas and "activo" not in columnas:
            raise DAOError("Esta base es de una versión anterior. Use una base nueva: ecotech_uml8.")
        for sentencia in (TABLAS_MYSQL if es_mysql else TABLAS_SQLITE):
            cursor.execute(sentencia)
        if es_mysql:
            cursor.execute(
                "SELECT 1 FROM information_schema.TABLE_CONSTRAINTS "
                "WHERE CONSTRAINT_SCHEMA = DATABASE() AND TABLE_NAME = 'departamento' "
                "AND CONSTRAINT_NAME = 'fk_departamento_gerente'")
            if cursor.fetchone() is None:
                cursor.execute(
                    "ALTER TABLE departamento ADD CONSTRAINT fk_departamento_gerente "
                    "FOREIGN KEY (id_gerente) REFERENCES empleado(id_empleado) ON DELETE RESTRICT")
        # La base guarda una comprobación para detectar una clave cambiada por error.
        cursor.execute("SELECT valor FROM configuracion WHERE clave = 'control_cifrado'")
        fila = cursor.fetchone()
        if fila is None:
            p = marcador_sql()
            cursor.execute(f"INSERT INTO configuracion (clave, valor) VALUES ({p}, {p})",
                           ("control_cifrado", seguridad.cifrar("EcoTech UML 8")))
        elif seguridad.descifrar(fila[0]) != "EcoTech UML 8":
            raise DAOError("La clave de cifrado no corresponde a esta base.")


if __name__ == "__main__":
    crear_tablas()
    print("Base de datos preparada.")
