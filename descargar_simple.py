"""
Script Simple de Descarga - Sentinel-2 con Google Earth Engine
Pregunta índices y periodos (YYYYMM), luego descarga las imágenes de cada periodo.

- La base completa se descarga una sola vez (ej. 202201-202608).
- Corridas posteriores solo bajan los periodos faltantes (manifest.json).
- Se pueden re-descargar periodos concretos con el modo "reemplazar"
  (ej. 202609,202601) si los datos se dañaron.
"""

import shutil
from pathlib import Path
from sentinel_downloader.gee_downloader import GEEDownloader
from sentinel_downloader.manifiesto import (
    Manifiesto,
    expandir_periodos,
    rango_fechas_periodo,
    carpetas_de_periodo,
)
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Colores para terminal
class C:
    G = '\033[92m'  # Verde
    Y = '\033[93m'  # Amarillo
    R = '\033[91m'  # Rojo
    B = '\033[94m'  # Azul
    E = '\033[0m'   # Reset

print(f"\n{C.B}{'='*60}")
print("   DESCARGADOR SENTINEL-2 - ÍNDICES DE VEGETACIÓN")
print(f"{'='*60}{C.E}\n")

# 1. SELECCIÓN DE ÍNDICES
# Mapeo de índices
indices_map = {
    '1': 'NDVI',
    '2': 'NDRE',
    '3': 'MSAVI',
    '4': 'RECI',
    '5': 'NDMI'
}

indices_seleccionados = []
while not indices_seleccionados:
    print(f"{C.Y}ÍNDICES DISPONIBLES:{C.E}")
    print("  1. NDVI  - Índice de Vegetación Normalizado")
    print("  2. NDRE  - Red Edge Normalizado")
    print("  3. MSAVI - Índice Ajustado de Vegetación")
    print("  4. RECI  - Índice de Clorofila Red Edge")
    print("  5. NDMI  - Índice de Humedad")
    print()
    
    seleccion = input(f"{C.G}Ingresa los números separados por comas (ej: 1,2,5): {C.E}").strip()
    
    for num in seleccion.split(','):
        num = num.strip()
        if num in indices_map:
            indices_seleccionados.append(indices_map[num])
    
    if not indices_seleccionados:
        print(f"{C.R}[ERROR] No se seleccionó ningún índice válido. Intenta de nuevo.{C.E}\n")

print(f"{C.G}[OK] Índices seleccionados: {', '.join(indices_seleccionados)}{C.E}\n")

# 2. SELECCIÓN DE PERIODOS (YYYYMM)
periodos = []
while not periodos:
    print(f"{C.Y}PERIODOS A DESCARGAR (formato YYYYMM):{C.E}")
    print("  Rango:  202201-202608   (todos los meses entre ambos)")
    print("  Lista:  202609,202601   (solo esos meses)")
    print("  Mezcla: 202201-202203,202609")
    print()
    entrada = input(f"{C.G}Periodos: {C.E}").strip()
    try:
        periodos = expandir_periodos(entrada)
    except ValueError as e:
        print(f"{C.R}[ERROR] {e}. Intenta de nuevo.{C.E}\n")

print(f"{C.G}[OK] {len(periodos)} periodo(s): {periodos[0]} → {periodos[-1]}{C.E}")
if len(periodos) <= 12:
    print(f"  {', '.join(periodos)}")
print()

# 2b. MODO: solo faltantes (por defecto) o reemplazar
print(f"{C.Y}MODO DE DESCARGA:{C.E}")
print("  1. Solo faltantes  - omite periodos/imágenes ya descargados (recomendado)")
print("  2. Reemplazar      - borra y vuelve a descargar los periodos indicados")
print()
modo = None
while modo not in ['1', '2', '']:
    modo = input(f"{C.G}Selecciona el modo [1]: {C.E}").strip()
    if modo not in ['1', '2', '']:
        print(f"{C.R}[ERROR] Opción inválida.{C.E}")
reemplazar = (modo == '2')
print(f"{C.G}[OK] Modo: {'REEMPLAZAR' if reemplazar else 'solo faltantes'}{C.E}\n")

# 3. SELECCIÓN DE SHAPEFILE
# Buscar todos los shapefiles
shapefiles_dir = Path("shapefiles")
todos_los_shp = list(shapefiles_dir.glob("**/*.shp"))

# Filtrar solo shapefiles válidos (que tengan .shx, .dbf, etc.)
shapefiles = []
for shp in todos_los_shp:
    # Verificar que existan los archivos complementarios mínimos
    shx_file = shp.with_suffix('.shx')
    dbf_file = shp.with_suffix('.dbf')
    
    if shx_file.exists() and dbf_file.exists():
        shapefiles.append(shp)
    else:
        print(f"{C.Y}[AVISO] Shapefile incompleto omitido: {shp.name} (falta .shx o .dbf){C.E}")

if not shapefiles:
    print(f"{C.R}[ERROR] No se encontró ningún shapefile válido en shapefiles/{C.E}")
    print(f"{C.Y}Asegúrate de que tu shapefile tenga todos los archivos: .shp, .shx, .dbf, .prj{C.E}")
    exit(1)

shapefile_seleccionado = None
shapefile_path = None

while shapefile_seleccionado is None:
    print(f"{C.Y}ÁREAS DISPONIBLES:{C.E}")
    
    # Mostrar shapefiles disponibles con nombre de carpeta si está en subcarpeta
    for idx, shp in enumerate(shapefiles, 1):
        # Si está en una subcarpeta, mostrar el nombre de la carpeta
        if shp.parent != shapefiles_dir:
            nombre_display = shp.parent.name
        else:
            nombre_display = shp.stem
        print(f"  {idx}. {nombre_display}")
    
    print()
    seleccion_shp = input(f"{C.G}Selecciona el número del área a usar: {C.E}").strip()
    
    try:
        idx_shp = int(seleccion_shp) - 1
        if idx_shp < 0 or idx_shp >= len(shapefiles):
            print(f"{C.R}[ERROR] Número inválido. Debe estar entre 1 y {len(shapefiles)}. Intenta de nuevo.{C.E}\n")
            continue
        
        shapefile_seleccionado = shapefiles[idx_shp]
        shapefile_path = str(shapefile_seleccionado)
        
        # Mostrar nombre de carpeta en la confirmación también
        if shapefile_seleccionado.parent != shapefiles_dir:
            nombre_confirmacion = shapefile_seleccionado.parent.name
        else:
            nombre_confirmacion = shapefile_seleccionado.stem
        print(f"{C.G}[OK] Área seleccionada: {nombre_confirmacion}{C.E}\n")
        
    except ValueError:
        print(f"{C.R}[ERROR] Debes ingresar un número válido. Intenta de nuevo.{C.E}\n")

# 4. CONFIRMACIÓN
print(f"{C.B}{'='*60}")
print("RESUMEN DE DESCARGA:")
print(f"{'='*60}{C.E}")
# Mostrar nombre de carpeta consistente
if shapefile_seleccionado.parent != shapefiles_dir:
    nombre_area = shapefile_seleccionado.parent.name
else:
    nombre_area = shapefile_seleccionado.stem
print(f"  Área:     {nombre_area}")
print(f"  Índices:  {', '.join(indices_seleccionados)}")
print(f"  Periodos: {periodos[0]} → {periodos[-1]} ({len(periodos)} meses)")
print(f"  Modo:     {'REEMPLAZAR (borra y re-descarga)' if reemplazar else 'solo faltantes'}")
print(f"  Total:    {len(indices_seleccionados) * len(periodos)} combinaciones índice×periodo")
print()

# Consultar manifiesto para anticipar qué se omitirá
manifiesto = Manifiesto(Path("descargas") / nombre_area)
agregados = manifiesto.reconstruir_desde_disco()
if agregados:
    manifiesto.guardar()
    print(f"{C.Y}ℹ Manifiesto reconstruido desde disco: {agregados} periodo(s) ya descargados registrados{C.E}")

if not reemplazar:
    ya_completos = [
        (idx, per) for idx in indices_seleccionados for per in periodos
        if manifiesto.esta_completo(idx, per)
    ]
    pendientes = len(indices_seleccionados) * len(periodos) - len(ya_completos)
    print(f"  Ya completos (se omiten): {len(ya_completos)}")
    print(f"  Por descargar:            {pendientes}")
    print()
    if pendientes == 0:
        print(f"{C.G}[OK] Todo lo solicitado ya está descargado. Nada que hacer.{C.E}")
        print(f"{C.Y}  Usa el modo 'Reemplazar' si necesitas volver a bajar algún periodo.{C.E}\n")
        exit(0)

confirmar = input(f"{C.Y}¿Continuar con la descarga? (s/n): {C.E}").strip().lower()

if confirmar != 's':
    print(f"{C.Y}[CANCELADO] Descarga cancelada por el usuario{C.E}")
    exit(0)

# 5. EJECUCIÓN DE DESCARGAS
print(f"\n{C.B}{'='*60}")
print("INICIANDO DESCARGAS...")
print(f"{'='*60}{C.E}\n")

try:
    descargador = GEEDownloader()
    carpeta_area = Path("descargas") / nombre_area

    total = len(indices_seleccionados) * len(periodos)
    n = 0
    resumen = {'descargadas': 0, 'omitidas': 0, 'fallidas': 0,
               'periodos_omitidos': 0, 'periodos_sin_imagenes': 0}

    for indice in indices_seleccionados:
        print(f"\n{C.B}══ {indice} ══{C.E}")
        carpeta_indice = carpeta_area / indice

        for periodo in periodos:
            n += 1
            etiqueta = f"[{n}/{total}] {indice} {periodo}"

            if not reemplazar and manifiesto.esta_completo(indice, periodo):
                print(f"{C.Y}{etiqueta}: ya completo, omitido{C.E}")
                resumen['periodos_omitidos'] += 1
                continue

            if reemplazar:
                viejas = carpetas_de_periodo(carpeta_indice, periodo)
                for carpeta in viejas:
                    shutil.rmtree(carpeta)
                if viejas:
                    print(f"{C.Y}{etiqueta}: {len(viejas)} carpeta(s) previas eliminadas{C.E}")

            fecha_inicio_str, fecha_fin_str = rango_fechas_periodo(periodo)
            print(f"{C.Y}{etiqueta}: descargando {fecha_inicio_str} → {fecha_fin_str}{C.E}")

            resultado = descargador.descargar_indice(
                shapefile_path=shapefile_path,
                indice=indice,
                fecha_inicio=fecha_inicio_str,
                fecha_fin=fecha_fin_str,
                nombre_area=nombre_area,
                max_cloud=30,
                omitir_existentes=not reemplazar,
            )

            if not resultado['exito']:
                print(f"{C.R}[ERROR] {etiqueta}: {resultado.get('error', 'Desconocido')}{C.E}")
                resumen['fallidas'] += 1
                continue

            exitosos = resultado['exitosos']
            fallidos = resultado['fallidos']
            omitidos = resultado.get('omitidos', 0)
            fechas = resultado.get('fechas', [])

            if resultado.get('sin_imagenes'):
                print(f"{C.Y}  [AVISO] Sin imágenes disponibles (nubes > 30% o sin pasadas){C.E}")
                resumen['periodos_sin_imagenes'] += 1
            else:
                print(f"{C.G}  [OK] {exitosos} descargadas, {omitidos} ya existían, {fallidos} fallidas{C.E}")

            resumen['descargadas'] += exitosos
            resumen['omitidas'] += omitidos
            resumen['fallidas'] += fallidos

            # Registrar en manifiesto (aun con 0 imágenes: el periodo se consultó)
            manifiesto.registrar(indice, periodo, fechas, exitosos + omitidos, fallidos,
                                 reemplazo=reemplazar)
            manifiesto.guardar()

    print(f"\n{C.B}{'='*60}")
    print("PROCESO COMPLETADO")
    print(f"{'='*60}{C.E}")
    print(f"  Imágenes descargadas:   {resumen['descargadas']}")
    print(f"  Imágenes ya existentes: {resumen['omitidas']}")
    print(f"  Imágenes fallidas:      {resumen['fallidas']}")
    print(f"  Periodos omitidos:      {resumen['periodos_omitidos']} (ya completos)")
    print(f"  Periodos sin imágenes:  {resumen['periodos_sin_imagenes']}")
    print()
    print(f"{C.G}Las descargas están en: descargas/{nombre_area}/{C.E}")
    print(f"{C.G}Manifiesto: {manifiesto.ruta}{C.E}")
    if reemplazar:
        print(f"{C.Y}Los periodos reemplazados quedaron marcados para recalcular en el análisis{C.E}")
    print(f"{C.G}Para extraer píxeles, ejecuta: python extraer_pixeles.py{C.E}\n")

except Exception as e:
    print(f"\n{C.R}[ERROR] ERROR CRÍTICO: {e}{C.E}")
    print(f"{C.Y}Verifica:{C.E}")
    print(f"  1. Archivo JSON de service account (tesis-*.json) en la carpeta raíz")
    print(f"  2. Shapefile en carpeta shapefiles/")
    print(f"  3. Periodos válidos en formato YYYYMM\n")
    exit(1)
