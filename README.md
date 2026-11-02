# Preparar y ejecutar

Necesitas Python 3.10 o superior y Git. La configuración inicial utiliza
SQLite, por lo que no necesitas instalar WampServer ni MariaDB.

Ejecuta los comandos en la terminal, uno por uno y en el orden indicado.
Si un paso muestra un error, soluciónalo antes de continuar.

# 1. Descargar el proyecto

```bash
git clone https://github.com/Faxi1r/IgnacioRios_POOS_Ecotech.git
cd IgnacioRios_POOS_Ecotech
```

Si ya tienes el proyecto descargado, abre su carpeta en VS Code y selecciona
Terminal → Nueva terminal. Debes estar en la carpeta que contiene
`README.md`, `requirements.txt`, `scripts/` y `src/`.

# 2. Crear el entorno de Python

Esto crea la carpeta `.venv`, donde se instalarán las bibliotecas del proyecto.

Linux:

```bash
python3 -m venv .venv
```

Windows / PowerShell:

```powershell
python -m venv .venv
```

Los siguientes comandos usan directamente el Python de `.venv`.
No es necesario activar el entorno por separado.

# 3. Instalar las dependencias

Linux:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Windows / PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Espera a que termine la instalación antes de continuar.

# 4. Crear el archivo .env y la clave de cifrado

Este paso se realiza después de instalar las dependencias y antes de
crear los datos de ejemplo o abrir el programa.

Linux:

```bash
.venv/bin/python scripts/preparar_entorno.py
```

Windows / PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts/preparar_entorno.py
```

El script copia la configuración de `.env.example` a un nuevo `.env`
y genera una clave de cifrado. Si `.env` ya existe, lo conserva.

No basta con cambiar el nombre de `.env.example`: también se necesita
una clave válida, que este script genera.

# 5. Crear la base de datos y cargar los ejemplos

Linux:

```bash
.venv/bin/python -m src.main --semilla
```

Windows / PowerShell:

```powershell
.\.venv\Scripts\python.exe -m src.main --semilla
```

Con la configuración predeterminada, se crea `ecotech_uml8.db`,
sus tablas y los datos de práctica.

Cuentas de ejemplo:

| Usuario | Contraseña inicial |
|---|---|
| admin_demo | Demo2026* |
| ana_demo | Demo2026* |

Repetir este comando no duplica los ejemplos ni restablece las contraseñas.

# 6. Iniciar el programa

Linux:

```bash
.venv/bin/python -m src.main
```

Windows / PowerShell:

```powershell
.\.venv\Scripts\python.exe -m src.main
```

Ingresa una de las cuentas anteriores. La contraseña no se muestra
mientras la escribes; es normalpara más seguridad.

### Para abrirlo otro día

Entra en la carpeta del proyecto y ejecuta solamente el comando del paso 6.
No necesitas crear nuevamente el entorno, el `.env` ni los datos de ejemplo.

Conserva el `.env` junto con tu base de datos: su clave permite leer los
datos cifrados. No subas el `.env`, la carpeta `.venv` ni la base de datos
a GitHub.
