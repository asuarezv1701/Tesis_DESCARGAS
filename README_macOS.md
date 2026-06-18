# Descargador de Imágenes Sentinel-2 - Instrucciones para macOS/Linux

Sistema para descargar y analizar imágenes satelitales de vegetación usando Google Earth Engine.

---

## Instalación rápida para macOS

### Paso 1: Verificar Python

```bash
# Verificar que tienes Python 3.10 o superior
python3 --version

# Si no tienes Python instalado, descárgalo desde python.org
# o instálalo con Homebrew:
brew install python@3.10
```

### Paso 2: Crear ambiente virtual

```bash
# Navegar a la carpeta del proyecto
cd ~/Developer/TT/Tesis_DESCARGAS

# Crear ambiente virtual
python3 -m venv venv

# Activar el ambiente virtual
source venv/bin/activate

# Instalar todas las dependencias
pip install -r requirements.txt
```

### Paso 3: Configurar credenciales

Coloca tu archivo JSON de credenciales de Google Earth Engine en la carpeta principal del proyecto. El archivo debe tener un nombre que empiece con `tesis-` (por ejemplo: `tesis-123456-abc.json`).

O configura las variables de entorno:

```bash
export SENTINEL_CLIENT_ID='tu_client_id'
export SENTINEL_CLIENT_SECRET='tu_client_secret'
```

Para hacerlo permanente, agrégalas a tu `~/.zshrc` o `~/.bash_profile`:

```bash
echo 'export SENTINEL_CLIENT_ID="tu_client_id"' >> ~/.zshrc
echo 'export SENTINEL_CLIENT_SECRET="tu_client_secret"' >> ~/.zshrc
source ~/.zshrc
```

### Paso 4: Agregar shapefile

El proyecto ya incluye un shapefile de ejemplo en `shapefiles/UPIITA_contours_25nov.2025/`.

---

## Cómo usar el programa (macOS)

```bash
# Activar ambiente virtual
source venv/bin/activate

# Ejecutar el programa principal
python inicio.py
```

### Comandos disponibles

```bash
python inicio.py              # Proceso completo interactivo
python main.py                # Descarga con menú interactivo
python extraer_pixeles.py     # Extraer píxeles de imágenes
python visualizar_indices.py  # Visualizar índices
python verificar_sistema.py   # Verificar configuración
```

---

## Verificar instalación

```bash
# Activar el ambiente
source venv/bin/activate

# Verificar el sistema completo
python verificar_sistema_completo.py
```

Este script verificará:
- ✓ Versión de Python
- ✓ Dependencias instaladas
- ✓ Credenciales configuradas
- ✓ Shapefiles disponibles

---

## Desactivar el ambiente virtual

Cuando termines de trabajar:

```bash
deactivate
```

---

## Solución de problemas en macOS

### Error: "command not found: python"

Usa `python3` en lugar de `python`:

```bash
python3 -m venv venv
python3 inicio.py
```

### Error al instalar GDAL/rasterio

Si tienes problemas instalando dependencias geoespaciales:

```bash
# Instalar GDAL con Homebrew primero
brew install gdal

# Luego instalar las dependencias de Python
pip install -r requirements.txt
```

O usa Conda (ver NOTAS_CONDA.txt en la raíz del proyecto).

### Error: "ModuleNotFoundError"

Asegúrate de que el ambiente virtual está activado:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

## Rutas de archivos en macOS

En macOS, las rutas usan `/` en lugar de `\`:

```python
# ✓ Correcto
shapefile_path = "shapefiles/UPIITA_contours_25nov.2025/UPIITA_contours_25Nov2025.shp"

# ✗ Incorrecto (estilo Windows)
shapefile_path = r"C:\ruta\a\tu\shapefile.shp"
```

---

## Notas adicionales

- Todos los scripts Python son compatibles con macOS sin modificaciones
- Las rutas se manejan automáticamente usando `pathlib.Path`
- Usa el mismo ambiente virtual para ambos procesos (DESCARGAS y ANALISIS)

Para más detalles sobre el uso del programa, consulta el README.md principal.
