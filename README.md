# EcoTech

Programa de consola para empleados, departamentos, proyectos, horas, cuentas e informes. Incluye validaciones de Empleado y consulta del dólar observado.

## Preparar y ejecutar

Abre esta carpeta en VS Code. Usa Python 3.10 o superior. Si todavía no tienes un entorno, créalo con los comandos de tu sistema.

Linux / EndeavourOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/preparar_entorno.py
.venv/bin/python -m src.main --semilla
.venv/bin/python -m src.main
```

Windows / PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/preparar_entorno.py
.\.venv\Scripts\python.exe -m src.main --semilla
.\.venv\Scripts\python.exe -m src.main
```

Selecciona el intérprete de .venv en VS Code. SQLite crea ecotech_uml8.db sin necesitar WampServer. El script genera .env con una clave propia; conserva uno existente. Si ya preparaste el entorno, puedes empezar por el comando de inicio.

Cuentas iniciales de práctica: admin_demo y ana_demo, contraseña Demo2026*. La contraseña no aparece mientras escribes. Repetir --semilla no duplica ejemplos ni restablece contraseñas. Para una base sin ejemplos usa --crear-admin en lugar de --semilla.

## Qué probar

- Registra un empleado: A se rechaza como nombre; Ana se acepta.
- Un correo como ana@empresa..cl se rechaza; se vuelve a pedir solo ese campo.
- La opción 7 del menú administrativo consulta el dólar. Muestra fecha del registro, CLP por USD y origen. Necesita Internet; los errores se muestran sin cerrar el sistema.
- Los informes se exportan desde su menú y quedan en reportes/.

## Configuración y bases existentes

DB_ENGINE elige sqlite o mysql. DB_NAME indica el archivo SQLite o la base MySQL. DB_HOST, DB_PORT, DB_USER y DB_PASSWORD se usan con MySQL. ECOTECH_CLAVE_CIFRADO permite leer los datos cifrados. Las variables de la terminal tienen prioridad sobre .env.

Si mantienes una base existente, conserva su .env y su clave. Antes de actualizar, corrige desde la versión anterior los nombres de una letra y correos que incumplan las reglas nuevas: también se revisan al recuperar empleados. Puedes practicar con un DB_NAME nuevo sin borrar la base anterior. No se realiza una migración automática de datos.

Para MySQL/MariaDB crea una base nueva ecotech_uml8, concede permisos a tu usuario y completa .env. El programa crea las tablas. Cambiar el motor no copia los datos de SQLite. WampServer es una opción para disponer de ese servidor en Windows; phpMyAdmin sirve para administrarlo, no para ejecutar Python.

## Comprobaciones

Con el Python del entorno:

```bash
python -m src.main --comprobar-conexion
python -m pip install -r requirements-dev.txt
python scripts/verificar.py
```

En Windows usa .\.venv\Scripts\python.exe; en Linux, .venv/bin/python. Los tests usan SQLite temporal y respuestas HTTP simuladas. Los resultados guardados y el intento de consulta real están en docs/RESULTADOS_PRUEBAS.txt y docs/CONSULTA_HTTP.txt. No se probó contra un servidor MySQL real.

## Archivos

- src/dependencia/: ocho clases y reglas del dominio.
- src/menus/: preguntas, opciones y mensajes.
- src/persistencia/: conexión, tablas, DAO y semillas.
