import os
import unittest
from unittest.mock import patch

from cryptography.fernet import Fernet
from src.dependencia import Seguridad, Usuario
from src.persistencia import crear_tablas
from tests.apoyo import BaseBD


class SeguridadTest(unittest.TestCase):
    def test_hash_no_es_clave_y_usa_sal_distinta(self):
        seguridad = Seguridad()
        uno = seguridad.hashear_contrasena("Clave2026*")
        dos = seguridad.hashear_contrasena("Clave2026*")
        self.assertNotEqual(uno, dos)
        self.assertNotIn("Clave2026*", uno)
        self.assertTrue(seguridad.verificar_contrasena("Clave2026*", uno))
        self.assertFalse(seguridad.verificar_contrasena("Otra2026*", uno))

    def test_hash_roto_y_contrasenas_debiles_no_se_aceptan(self):
        seguridad = Seguridad()
        for valor in ("", "12345678", "sololetras", "Ab1"):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                seguridad.hashear_contrasena(valor)
        for valor in ("hash_inventado", "", None, "pbkdf2_sha256$1$xx$zz"):
            self.assertFalse(seguridad.verificar_contrasena("Clave2026*", valor))

    def test_cifrado_recupera_unicode_y_cambia_en_cada_llamada(self):
        with patch.dict(os.environ, {"ECOTECH_CLAVE_CIFRADO": Fernet.generate_key().decode()}):
            seguridad = Seguridad()
            texto = "José Muñoz, dirección Ñuñoa 10, salario 900000"
            uno, dos = seguridad.cifrar(texto), seguridad.cifrar(texto)
            self.assertNotEqual(uno, dos)
            self.assertNotIn("José", uno)
            self.assertEqual(seguridad.descifrar(uno), texto)

    def test_otro_key_o_texto_adulterado_no_se_descifra(self):
        with patch.dict(os.environ, {"ECOTECH_CLAVE_CIFRADO": Fernet.generate_key().decode()}):
            token = Seguridad().cifrar("dato personal")
            with self.assertRaises(ValueError):
                Seguridad().descifrar(token[:-8] + "ABCDEFGH")
        with patch.dict(os.environ, {"ECOTECH_CLAVE_CIFRADO": Fernet.generate_key().decode()}):
            with self.assertRaises(ValueError):
                Seguridad().descifrar(token)

    def test_clave_faltante_o_invalida_informa_como_configurar(self):
        for valor in ("", "GENERAR_CON_EL_SCRIPT", "no-es-una-clave"):
            with self.subTest(valor=valor), patch.dict(os.environ, {"ECOTECH_CLAVE_CIFRADO": valor}):
                with self.assertRaises(ValueError):
                    Seguridad().cifrar("dato")

    def test_representacion_de_usuario_no_muestra_hash(self):
        usuario = Usuario(None, "prueba")
        usuario.establecer_contrasena("Clave2026*")
        self.assertNotIn(usuario.contrasena_hash, str(usuario))
        self.assertNotIn("Clave2026*", str(usuario))


class ClaveBaseTest(BaseBD):
    def test_base_rechaza_cambio_de_clave_sin_modificar_sus_datos(self):
        persona = self.persona()
        anterior = self.base.read_bytes()
        with patch.dict(os.environ, {"ECOTECH_CLAVE_CIFRADO": Fernet.generate_key().decode()}):
            with self.assertRaises(ValueError):
                crear_tablas()
        self.assertEqual(self.base.read_bytes(), anterior)
        from src.persistencia import EmpleadoDAO
        self.assertEqual(EmpleadoDAO.buscar_por_id(persona.id_empleado).nombre, persona.nombre)
