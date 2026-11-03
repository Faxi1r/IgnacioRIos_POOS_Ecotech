from .usuario import Usuario
from .informe import Informe


class Administrador(Usuario):
    def __init__(self, id_usuario, nombre_usuario, contrasena_hash="", activo=True, rol="admin"):
        if rol != "admin":
            raise ValueError("Un administrador debe tener rol admin.")
        super().__init__(id_usuario, nombre_usuario, contrasena_hash, activo, rol)

    def puede_acceder(self, modulo: str) -> bool:
        return (
            self.activo
            and self.rol == "admin"
            and modulo
            in {
                "empleados",
                "departamentos",
                "proyectos",
                "registros",
                "usuarios",
                "informes",
                "mi_cuenta",
            }
        )

    def generar_informe(self, tipo: str, empleados, departamentos, proyectos, registros) -> Informe:
        if not self.puede_acceder("informes"):
            raise ValueError("La cuenta está desactivada.")
        informe = Informe(None, tipo, creado_por=self.id_usuario)
        informe.generar(empleados, departamentos, proyectos, registros)
        return informe
