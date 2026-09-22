# Descargador de Imágenes Sentinel-2

Descarga imágenes satelitales de tu área de estudio y calcula automáticamente cinco índices
de vegetación. Funciona en **Windows, macOS y Linux**.

---

## ¿Qué hace este programa?

A partir de un polígono que tú defines, el sistema:

1. Busca todas las imágenes Sentinel-2 disponibles en el rango de fechas que elijas.
2. Calcula cinco índices de vegetación sobre cada imagen.
3. Extrae el valor de cada píxel a tablas que puedes abrir en Excel.
4. Genera mapas de colores listos para interpretar.

### Los cinco índices

| Índice | Qué mide | Para qué sirve |
|--------|----------|----------------|
| **NDVI** | Vigor general de la vegetación | Estado de salud global |
| **NDRE** | Clorofila y nitrógeno | Detecta estrés antes de que sea visible |
| **MSAVI** | Cobertura, descontando el suelo | Útil con vegetación escasa |
| **RECI** | Concentración de clorofila | Evaluación nutricional |
| **NDMI** | Contenido de agua en la hoja | Estrés hídrico |

> **Descarga incremental.** El sistema lleva un registro (`manifest.json`) de lo ya
> descargado. La primera ejecución baja toda la base; las siguientes sólo traen lo que falta.

---

## Antes de empezar

Necesitas tres cosas:

| Requisito | Detalle |
|-----------|---------|
| **Python 3.11 – 3.13** | Recomendado 3.12. Verifica con `python3 --version` |
| **Credenciales de Google Earth Engine** | Archivo JSON de cuenta de servicio |
| **Shapefile de tu área** | Los cuatro archivos: `.shp`, `.shx`, `.dbf`, `.prj` |

> **Sobre Python.** Se recomienda 3.12 porque las bibliotecas geoespaciales ya no publican
> versiones nuevas para 3.10, y en sistemas operativos recientes las versiones antiguas dejan
> de funcionar.

---

## Instalación

Estos pasos se realizan **una sola vez**.

### Paso 1 · Crear el ambiente virtual

<details open>
<summary><b>macOS / Linux</b></summary>

```bash
cd ruta/al/proyecto/Tesis_DESCARGAS
python3.12 -m venv venv
source venv/bin/activate
```
</details>

<details>
<summary><b>Windows (PowerShell)</b></summary>

```powershell
cd ruta\al\proyecto\Tesis_DESCARGAS
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```
</details>

> Debes activar el ambiente **cada vez** que abras una terminal nueva. Sabrás que está activo
> porque el prompt empieza con `(venv)`.

### Paso 2 · Instalar las librerías

```bash
pip install -r requirements.txt
```

### Paso 3 · Colocar tus credenciales

Copia el archivo JSON de Google Earth Engine en la carpeta principal del proyecto. Su nombre
debe empezar con `tesis-` (por ejemplo, `tesis-123456-abc.json`).

> **Importante:** ese archivo es una credencial privada. Ya está listado en `.gitignore` para
> que no se suba por accidente, pero tampoco lo incluyas al entregar el proyecto.

### Paso 4 · Colocar tu shapefile

Copia los cuatro archivos de tu shapefile dentro de `shapefiles/`. Si falta alguno, el
programa lo detecta y avisa.

### Paso 5 · Comprobar que todo quedó bien

```bash
python verificar_sistema.py
```

Debe mostrar `[OK]` en cada dependencia.

---

## Cómo usarlo

### La forma sencilla

```bash
python inicio.py
```

Este script te guía por los tres pasos del proceso (descarga, extracción y visualización),
pidiendo confirmación antes de cada uno.

Durante la descarga te hará cuatro preguntas:

**1. Qué índices quieres** — números separados por comas:

```
Ingresa los números separados por comas (ej: 1,2,5): 1,5
```

**2. Qué periodos descargar** — en formato `AAAAMM`. Acepta tres notaciones:

| Notación | Ejemplo | Significado |
|----------|---------|-------------|
| Rango | `202201-202608` | Todos los meses entre ambos |
| Lista | `202609,202601` | Sólo esos meses |
| Mezcla | `202201-202203,202609` | Combinación de las anteriores |

**3. Modo de descarga:**

| Modo | Comportamiento | Cuándo usarlo |
|------|----------------|---------------|
| **1 · Solo faltantes** *(por defecto)* | Omite lo ya descargado, según el manifiesto | Uso normal |
| **2 · Reemplazar** | Borra y vuelve a descargar los periodos indicados | Si sospechas que una descarga quedó corrupta |

**4. Qué área usar** — elige uno de los shapefiles disponibles en `shapefiles/`.

> Gracias al manifiesto, puedes pedir un rango amplio sin miedo: el programa descarga
> únicamente los periodos que aún no tiene.

### Ejecutar un paso por separado

```bash
python descargar_simple.py     # Sólo descargar imágenes
python extraer_pixeles.py      # Sólo extraer valores de píxeles
python visualizar_indices.py   # Sólo generar mapas
```

---

## Dónde quedan tus resultados

```
descargas/
└── NOMBRE_DE_TU_AREA/
    ├── manifest.json                    Registro de lo descargado
    └── NDVI/
        └── area_20250204_115050/
            ├── area_20250204_NDVI.tiff  Imagen satelital
            ├── valores_pixeles/
            │   ├── pixeles_NDVI.csv     Tabla para Excel
            │   └── pixeles_NDVI.shp     Capa para QGIS
            └── visualizacion/
                └── NDVI_clasificado.png Mapa de colores
```

| Extensión | Qué es | Con qué se abre |
|-----------|--------|-----------------|
| `.tiff` | Imagen satelital original | QGIS, ArcGIS |
| `.csv` | Tabla de valores por píxel | Excel, Python |
| `.shp` | Capa geográfica | QGIS, Google Earth |
| `.png` | Mapa de colores | Cualquier visor |

---

## Cómo leer los mapas

### NDVI — salud de la vegetación

| Color | Significado |
|-------|-------------|
| Café / marrón | Sin vegetación o muy seca |
| Amarillo | Vegetación débil o estresada |
| Verde claro | Moderadamente saludable |
| Verde | Saludable |
| Verde oscuro | Muy densa y saludable |

### NDMI — contenido de agua

| Color | Significado |
|-------|-------------|
| Café / marrón | Estrés hídrico severo |
| Beige | Poca humedad |
| Azul claro | Humedad moderada |
| Azul | Buena humedad |
| Azul oscuro | Alta humedad |

---

## Si algo sale mal

| Mensaje | Qué significa | Solución |
|---------|---------------|----------|
| `No se encontró archivo JSON` | Faltan las credenciales | Copia el JSON a la carpeta principal; su nombre debe empezar con `tesis-` |
| `No se encontró shapefile` | Falta el área de estudio | Copia los **cuatro** archivos (`.shp`, `.shx`, `.dbf`, `.prj`) a `shapefiles/` |
| `No hay imágenes disponibles` | Sin datos en ese rango | Amplía el rango de fechas o revisa que el shapefile cubra el área correcta |
| `ModuleNotFoundError` | Ambiente sin activar | Actívalo y reinstala: `pip install -r requirements.txt` |
| `command not found: python` | Alias distinto | Usa `python3` (macOS/Linux) o `py` (Windows) |

### Problemas al instalar GDAL o rasterio

En macOS, instala primero la librería del sistema:

```bash
brew install gdal
pip install -r requirements.txt
```

---

## Resumen rápido

```bash
source venv/bin/activate     # Windows: .\venv\Scripts\Activate.ps1
python inicio.py
# Revisa la carpeta descargas/
```

---

## Y después, ¿qué sigue?

Una vez descargados los datos, el proyecto **Tesis_ANALISIS** los procesa para generar
estadísticas, predicciones y reportes en PDF. Consulta su `README.md`.
