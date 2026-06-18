# Descargador de Imágenes Sentinel-2

Sistema para descargar y analizar imágenes satelitales de vegetación usando Google Earth Engine.

> **📱 Usuarios de macOS/Linux:** Las instrucciones de este README están enfocadas en Windows.  
> Para instrucciones específicas de macOS/Linux, consulta [README_macOS.md](README_macOS.md)

---

## ¿Qué hace este programa?

Este sistema descarga imágenes satelitales Sentinel-2 de cualquier zona del mundo y calcula automáticamente 5 índices de vegetación que te ayudan a analizar el estado de las plantas:

- **NDVI** - Mide la salud general de la vegetación
- **NDRE** - Detecta el nivel de clorofila en las hojas
- **MSAVI** - Útil cuando hay mucha tierra visible entre las plantas
- **RECI** - Mide clorofila con mayor precisión que NDVI
- **NDMI** - Indica el contenido de agua en la vegetación

El sistema descarga todas las imágenes disponibles en el rango de fechas que especifiques, no solo una imagen.

---

## Requisitos previos

Necesitas tener instalado en tu computadora:

1. **Python 3.10 o superior** - Descarga desde [python.org](https://www.python.org/downloads/)
2. **Credenciales de Google Earth Engine** - Archivo JSON con tus credenciales de acceso
3. **Shapefile de tu área de estudio** - Archivo .shp que define la zona geográfica a analizar

---

## Instalación

## Instalación

Estos pasos solo necesitas hacerlos una vez.

### Paso 1: Descargar el proyecto

Descarga el proyecto completo y descomprímelo en una carpeta de tu computadora.

### Paso 2: Instalar las dependencias

Abre PowerShell en la carpeta donde descargaste el proyecto y ejecuta estos comandos:

```powershell
# Crear un ambiente virtual de Python
python -m venv venv

# Activar el ambiente virtual
.\venv\Scripts\Activate.ps1

# Instalar todas las librerías necesarias
pip install -r requirements.txt
```

### Paso 3: Configurar tus credenciales

Coloca tu archivo JSON de credenciales de Google Earth Engine en la carpeta principal del proyecto. El archivo debe tener un nombre que empiece con `tesis-` (por ejemplo: `tesis-123456-abc.json`).

### Paso 4: Agregar tu shapefile

Coloca tu shapefile en la carpeta `shapefiles/`. Recuerda que un shapefile completo incluye varios archivos: .shp, .shx, .dbf, y .prj. Necesitas copiar todos estos archivos.

---

## Cómo usar el programa

### La forma más sencilla (recomendado)

Cada vez que quieras usar el programa, abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
# Primero activa el ambiente virtual
.\venv\Scripts\Activate.ps1

# Luego ejecuta el programa principal
python inicio.py
```

El programa te hará tres preguntas:

1. **¿Qué índices quieres descargar?** - Escribe los números separados por comas. Ejemplo: `1,5` para NDVI y NDMI
2. **¿Desde qué fecha?** - Escribe la fecha de inicio en formato YYYY-MM-DD. Ejemplo: `2025-02-01`
3. **¿Hasta qué fecha?** - Escribe la fecha final. Ejemplo: `2025-04-28`

Después de responder, el programa hará todo automáticamente:

- Busca y descarga todas las imágenes Sentinel-2 disponibles en ese rango de fechas
- Extrae los valores de cada píxel de las imágenes
- Crea mapas visuales con colores para cada índice
- Guarda todo en carpetas organizadas

El proceso puede tardar varios minutos dependiendo de cuántas imágenes encuentre.

---

## Dónde encontrar tus resultados

Todos los archivos se guardan en la carpeta `descargas/`. Dentro encontrarás una carpeta para cada índice (NDVI, NDRE, etc.), y dentro de cada una habrá una carpeta por cada imagen descargada.

Estructura de carpetas:

```
descargas/
├── NDVI/
│   ├── area_20250204_115050/
│   │   ├── area_20250204_NDVI.tiff          (Imagen satelital original)
│   │   ├── valores_pixeles/
│   │   │   ├── pixeles_NDVI.csv             (Tabla que puedes abrir en Excel)
│   │   │   └── pixeles_NDVI.shp             (Para usar en Google Earth o QGIS)
│   │   └── visualizacion/
│   │       └── NDVI_clasificado.png         (Mapa con colores)
│   └── (más carpetas con otras fechas)
```

Tipos de archivos que encontrarás:

- **Archivos .tiff** - Las imágenes satelitales originales
- **Archivos .csv** - Tablas con los datos que puedes abrir en Excel
- **Archivos .shp** - Shapefiles para visualizar en programas GIS como Google Earth o QGIS
- **Archivos .png** - Mapas visuales con colores

---

## Interpretación de los colores

Cuando abras las imágenes PNG, verás mapas con diferentes colores. Aquí está lo que significan:

### Para NDVI (salud de la vegetación)

- **Café/marrón**: No hay vegetación o está muy seca
- **Amarillo**: Vegetación débil o estresada
- **Verde claro**: Vegetación moderadamente saludable
- **Verde**: Vegetación saludable
- **Verde oscuro**: Vegetación muy densa y saludable

### Para NDMI (contenido de agua)

- **Café/marrón**: Vegetación muy seca, con estrés hídrico
- **Beige**: Poca humedad
- **Azul claro**: Humedad moderada
- **Azul**: Buena humedad
- **Azul oscuro**: Alta humedad

---

## Solución de problemas comunes

### Error: "No se encontró archivo JSON"

Esto significa que el programa no encuentra tus credenciales de Google Earth Engine. Verifica que colocaste el archivo JSON en la carpeta principal del proyecto y que su nombre empiece con `tesis-`.

### Error: "No se encontró shapefile"

El programa no encuentra tu shapefile. Asegúrate de que copiaste todos los archivos del shapefile (.shp, .shx, .dbf, .prj) en la carpeta `shapefiles/`.

### Error: "No hay imágenes disponibles"

No hay imágenes Sentinel-2 disponibles para tu área y rango de fechas. Puedes intentar:
- Ampliar el rango de fechas (usar más meses)
- Verificar que tu shapefile cubre el área correcta

---

## Ejemplo completo de uso

Aquí te muestro un ejemplo paso a paso de cómo usar el programa:

```powershell
# 1. Activar el ambiente virtual
.\venv\Scripts\Activate.ps1

# 2. Ejecutar el programa
python inicio.py

# 3. El programa pregunta: ¿Qué índices quieres?
# Tú escribes: 1
# (Esto descarga solo NDVI)

# 4. El programa pregunta: ¿Fecha de inicio?
# Tú escribes: 2025-01-01

# 5. El programa pregunta: ¿Fecha de fin?
# Tú escribes: 2025-03-31

# 6. Confirmas con: s

# 7. Esperas mientras el programa trabaja
# (Puede tardar varios minutos)

# 8. Cuando termine, revisa la carpeta descargas/NDVI/
```

---

## Resumen rápido

Si ya conoces el programa, estos son los pasos básicos:

1. Abre PowerShell en la carpeta del proyecto
2. Activa el ambiente: `.\venv\Scripts\Activate.ps1`
3. Ejecuta: `python inicio.py`
4. Responde las preguntas
5. Espera a que termine
6. Revisa la carpeta `descargas/`

---

**Última actualización:** 24 de noviembre de 2025  
**Sistema probado exitosamente con 18 imágenes descargadas**
