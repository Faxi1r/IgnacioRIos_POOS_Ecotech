from .usuario import Usuario
from .informe import Informe


class Administrador(Usuario):
    def puede_acceder(self, modulo: str) -> bool:
        return self.activo and modulo in {
            "empleados", "departamentos", "proyectos", "registros", "usuarios", "informes", "mi_cuenta",
        }

    def generar_informe(self, tipo: str, empleados, departamentos, proyectos, registros) -> Informe:
        if not self.puede_acceder("informes"):
            raise ValueError("La cuenta está desactivada.")
        informe = Informe(None, tipo, creado_por=self.id_usuario)
        informe.generar(empleados, departamentos, proyectos, registros)
        return informe
