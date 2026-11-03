import json
import sqlite3
from contextlib import closing
from datetime import date
from openpyxl import load_workbook
from pypdf import PdfReader

from src.dependencia import Departamento, Informe, RegistroDeTiempo
from src.persistencia import (
    DAOError,
    DepartamentoDAO,
    EmpleadoDAO,
    InformeDAO,
    ProyectoDAO,
    RegistroTiempoDAO,
    UsuarioDAO,
)
from tests.apoyo import BaseBD


class InformesTest(BaseBD):
    def setUp(self):
        super().setUp()
        self.admin = self.cuenta("admin_prueba", admin=True)
        self.ana = self.persona(nombre="José Muñoz")
        self.departamento = DepartamentoDAO.insertar(Departamento(None, "Tecnología", self.ana))
        self.trabajo = self.proyecto("Agua")
        ProyectoDAO.asignar_empleado(self.trabajo.id_proyecto, self.ana.id_empleado)
        self.registro = RegistroTiempoDAO.insertar(
            RegistroDeTiempo(
                None,
                date(2026, 3, 10),
                3.5,
                "Revisar sensores",
                self.ana.id_empleado,
                self.trabajo.id_proyecto,
            )
        )

    def generar(self):
        return self.admin.generar_informe(
            "Resumen",
            EmpleadoDAO.listar(),
            DepartamentoDAO.listar(),
            ProyectoDAO.listar(),
            RegistroTiempoDAO.listar(),
        )

    def test_incluye_cuatro_areas_total_fecha_y_autor(self):
        informe = InformeDAO.insertar(self.generar())
        leido = InformeDAO.buscar_por_id(informe.id_informe)
        datos = json.loads(leido.contenido)
        self.assertEqual(set(datos), {"empleados", "departamentos", "proyectos", "registros"})
        self.assertTrue(all(len(filas) == 1 for filas in datos.values()))
        self.assertEqual(datos["registros"][0][4], 3.5)
        self.assertEqual(leido.creado_por, self.admin.id_usuario)
        self.assertIn("Total de horas: 3.50", leido._texto_legible())
        self.assertEqual(leido.fecha_generacion, date.today())

    def test_ficha_horas_e_informe_se_guardan_cifrados(self):
        informe = InformeDAO.insertar(self.generar())
        with closing(sqlite3.connect(self.base)) as conexion, conexion:
            contenido = conexion.execute("SELECT contenido FROM informe").fetchone()[0]
            tareas = conexion.execute("SELECT descripcion_tareas FROM registro_tiempo").fetchone()[
                0
            ]
        self.assertNotIn("José", contenido)
        self.assertNotIn("Revisar sensores", tareas)
        self.assertEqual(InformeDAO.buscar_por_id(informe.id_informe).contenido, informe.contenido)

    def test_cambiar_datos_actuales_no_reescribe_el_informe_guardado(self):
        informe = InformeDAO.insertar(self.generar())
        contenido = informe.contenido
        self.ana.nombre = "Nombre nuevo"
        EmpleadoDAO.actualizar(self.ana)
        RegistroTiempoDAO.eliminar(self.registro.id_registro)
        self.assertEqual(InformeDAO.buscar_por_id(informe.id_informe).contenido, contenido)

    def test_recalcular_modifica_contenido_y_conserva_autor(self):
        informe = InformeDAO.insertar(self.generar())
        self.registro.horas = 7
        RegistroTiempoDAO.actualizar(self.registro)
        nuevo = self.generar()
        nuevo.id_informe = informe.id_informe
        self.assertTrue(InformeDAO.actualizar(nuevo))
        self.assertEqual(
            InformeDAO.buscar_por_id(informe.id_informe).creado_por, self.admin.id_usuario
        )
        self.assertIn("7.00", InformeDAO.buscar_por_id(informe.id_informe)._texto_legible())
        self.assertTrue(InformeDAO.eliminar(informe.id_informe))

    def test_informe_no_admite_usuario_comun_sin_autor_o_autor_inactivo(self):
        cuenta = self.cuenta("normal")
        for autor in (cuenta.id_usuario, None, 999):
            informe = self.generar()
            informe.creado_por = autor
            with self.subTest(autor=autor), self.assertRaises(DAOError):
                InformeDAO.insertar(informe)
        self.cuenta("respaldo", admin=True)
        self.admin.desactivar()
        UsuarioDAO.actualizar(self.admin)
        informe = Informe(None, "Resumen", creado_por=self.admin.id_usuario)
        informe.generar([], [], [], [])
        with self.assertRaises(DAOError):
            InformeDAO.insertar(informe)

    def test_desactivar_autor_conserva_su_relacion_y_no_se_cambia_por_otro(self):
        informe = InformeDAO.insertar(self.generar())
        segundo = self.cuenta("segundo_admin", admin=True)
        self.admin.desactivar()
        UsuarioDAO.actualizar(self.admin)
        self.assertEqual(
            InformeDAO.buscar_por_id(informe.id_informe).creado_por, self.admin.id_usuario
        )
        informe.creado_por = segundo.id_usuario
        with self.assertRaises(DAOError):
            InformeDAO.actualizar(informe)
        with closing(sqlite3.connect(self.base)) as conexion, conexion:
            conexion.execute("PRAGMA foreign_keys=ON")
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute(
                    "DELETE FROM administrador WHERE id_usuario=?", (self.admin.id_usuario,)
                )

    def test_exporta_pdf_legible_y_excel_con_valores_reales(self):
        informe = self.generar()
        pdf, excel = self.carpeta / "informe.pdf", self.carpeta / "informe.xlsx"
        informe.exportar_pdf(str(pdf))
        informe.exportar_excel(str(excel))
        texto = "\n".join(p.extract_text() for p in PdfReader(pdf).pages)
        for esperado in (
            "José Muñoz",
            "Tecnología",
            "Agua",
            "Revisar sensores",
            "3.50",
            "Departamentos",
        ):
            self.assertIn(esperado, texto)
        libro = load_workbook(excel)
        self.assertEqual(
            libro.sheetnames,
            ["Resumen", "Empleados", "Departamentos", "Proyectos", "Horas registradas"],
        )
        self.assertEqual(libro["Resumen"]["B4"].value, 3.5)
        self.assertEqual(libro["Empleados"]["H2"].value, 900000)
        self.assertEqual(libro["Horas registradas"]["E2"].value, 3.5)
        self.assertEqual(libro["Empleados"]["C2"].value, "José Muñoz")
        libro.close()

    def test_excel_trata_textos_con_igual_como_textos(self):
        self.ana.nombre = '=HYPERLINK("https://example.com")'
        EmpleadoDAO.actualizar(self.ana)
        informe = self.generar()
        informe.tipo = "=1+1"
        ruta = self.carpeta / "texto.xlsx"
        informe.exportar_excel(str(ruta))
        libro = load_workbook(ruta, data_only=False)
        self.assertEqual(libro["Empleados"]["C2"].data_type, "s")
        self.assertEqual(libro["Resumen"]["B1"].data_type, "s")
        libro.close()

    def test_informe_vacio_exporta_y_contenido_invalido_se_rechaza(self):
        informe = self.admin.generar_informe("Sin datos", [], [], [], [])
        informe.exportar_pdf(str(self.carpeta / "vacio.pdf"))
        informe.exportar_excel(str(self.carpeta / "vacio.xlsx"))
        self.assertIn("Total de horas: 0.00", informe._texto_legible())
        informe.contenido = "No es un contenido generado"
        with self.assertRaises(ValueError):
            InformeDAO.insertar(informe)
        with self.assertRaises(ValueError):
            informe.exportar_pdf(str(self.carpeta / "invalido.pdf"))

    def test_exportacion_exige_extension_correcta_y_no_cambia_contenido(self):
        informe = self.generar()
        anterior = informe.contenido
        for exportar, extension in (
            (informe.exportar_pdf, ".txt"),
            (informe.exportar_excel, ".csv"),
        ):
            with self.assertRaises(ValueError):
                exportar(str(self.carpeta / ("incorrecto" + extension)))
        self.assertEqual(informe.contenido, anterior)

    def test_pdf_largo_se_divide_en_paginas_sin_perder_el_final(self):
        for numero in range(20):
            RegistroTiempoDAO.insertar(
                RegistroDeTiempo(
                    None,
                    date(2026, 4, numero + 1),
                    2,
                    ("Descripción larga con acentos, revisión de sensores. " * 8)
                    + f" FIN{numero:02d}",
                    self.ana.id_empleado,
                    self.trabajo.id_proyecto,
                )
            )
        ruta = self.carpeta / "largo.pdf"
        self.generar().exportar_pdf(str(ruta))
        lector = PdfReader(ruta)
        self.assertGreater(len(lector.pages), 1)
        for pagina in lector.pages:
            self.assertLessEqual(pagina.extract_text().count("Tareas"), 1)
        texto = "\n".join(p.extract_text() for p in lector.pages)
        self.assertIn("FIN00", texto)
        self.assertIn("FIN19", texto)
