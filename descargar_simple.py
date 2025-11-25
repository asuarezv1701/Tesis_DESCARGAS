"""
Script Simple de Descarga - Sentinel-2 con Google Earth Engine
Pregunta índices y fechas, luego descarga múltiples imágenes
"""

from datetime import datetime, timedelta
from pathlib import Path
from sentinel_downloader.gee_downloader import GEEDownloader
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
        print(f"{C.R}✗ No se seleccionó ningún índice válido. Intenta de nuevo.{C.E}\n")

print(f"{C.G}✓ Índices seleccionados: {', '.join(indices_seleccionados)}{C.E}\n")

# 2. SELECCIÓN DE FECHAS
fecha_inicio = None
fecha_fin = None
diferencia = 0

while fecha_inicio is None or fecha_fin is None:
    print(f"{C.Y}RANGO DE FECHAS (mínimo 30 días):{C.E}")
    print("Formato: YYYY-MM-DD (ejemplo: 2025-10-01)")
    print()
    
    fecha_inicio_str = input(f"{C.G}Fecha de inicio: {C.E}").strip()
    fecha_fin_str = input(f"{C.G}Fecha de fin: {C.E}").strip()
    
    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
        fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d")
        
        # Validar que sea al menos 30 días
        diferencia = (fecha_fin - fecha_inicio).days
        
        if diferencia < 0:
            print(f"{C.R}✗ La fecha de fin debe ser posterior a la fecha de inicio. Intenta de nuevo.{C.E}\n")
            fecha_inicio = None
            fecha_fin = None
            continue
        
        if diferencia < 30:
            print(f"{C.R}✗ El rango debe ser de al menos 30 días (tienes {diferencia} días). Intenta de nuevo.{C.E}\n")
            fecha_inicio = None
            fecha_fin = None
            continue
        
        print(f"{C.G}✓ Rango: {fecha_inicio_str} a {fecha_fin_str} ({diferencia} días){C.E}\n")
        
    except ValueError as e:
        print(f"{C.R}✗ Error en el formato de fecha. Usa YYYY-MM-DD (ejemplo: 2025-10-01). Intenta de nuevo.{C.E}\n")
        fecha_inicio = None
        fecha_fin = None

# 3. SELECCIÓN DE SHAPEFILE
# Buscar todos los shapefiles
shapefiles_dir = Path("shapefiles")
shapefiles = list(shapefiles_dir.glob("**/*.shp"))

if not shapefiles:
    print(f"{C.R}✗ No se encontró ningún shapefile en shapefiles/{C.E}")
    print(f"{C.Y}Coloca tu shapefile (.shp) en la carpeta shapefiles/{C.E}")
    exit(1)

shapefile_seleccionado = None
shapefile_path = None

while shapefile_seleccionado is None:
    print(f"{C.Y}ÁREAS DISPONIBLES:{C.E}")
    
    # Mostrar shapefiles disponibles
    for idx, shp in enumerate(shapefiles, 1):
        print(f"  {idx}. {shp.stem}")
    
    print()
    seleccion_shp = input(f"{C.G}Selecciona el número del área a usar: {C.E}").strip()
    
    try:
        idx_shp = int(seleccion_shp) - 1
        if idx_shp < 0 or idx_shp >= len(shapefiles):
            print(f"{C.R}✗ Número inválido. Debe estar entre 1 y {len(shapefiles)}. Intenta de nuevo.{C.E}\n")
            continue
        
        shapefile_seleccionado = shapefiles[idx_shp]
        shapefile_path = str(shapefile_seleccionado)
        print(f"{C.G}✓ Área seleccionada: {shapefile_seleccionado.stem}{C.E}\n")
        
    except ValueError:
        print(f"{C.R}✗ Debes ingresar un número válido. Intenta de nuevo.{C.E}\n")

# 4. CONFIRMACIÓN
print(f"{C.B}{'='*60}")
print("RESUMEN DE DESCARGA:")
print(f"{'='*60}{C.E}")
print(f"  Área:    {shapefile_seleccionado.stem}")
print(f"  Índices: {', '.join(indices_seleccionados)}")
print(f"  Desde:   {fecha_inicio_str}")
print(f"  Hasta:   {fecha_fin_str}")
print(f"  Total:   {len(indices_seleccionados)} índices en {diferencia} días")
print()

confirmar = input(f"{C.Y}¿Continuar con la descarga? (s/n): {C.E}").strip().lower()

if confirmar != 's':
    print(f"{C.R}✗ Descarga cancelada{C.E}")
    exit(0)

# 5. EJECUCIÓN DE DESCARGAS
print(f"\n{C.B}{'='*60}")
print("INICIANDO DESCARGAS...")
print(f"{'='*60}{C.E}\n")

try:
    # Crear instancia del descargador de GEE
    descargador = GEEDownloader()
    
    # Descargar cada índice usando el shapefile seleccionado
    for i, indice in enumerate(indices_seleccionados, 1):
        print(f"\n{C.Y}[{i}/{len(indices_seleccionados)}] Descargando {indice}...{C.E}")
        
        resultado = descargador.descargar_indice(
            shapefile_path=shapefile_path,
            indice=indice,
            fecha_inicio=fecha_inicio_str,
            fecha_fin=fecha_fin_str,
            nombre_area=shapefile_seleccionado.stem,
            max_cloud=30
        )
        
        if resultado['exito']:
            print(f"{C.G}✓ {indice} completado:{C.E}")
            print(f"  - Imágenes descargadas: {resultado['exitosos']}/{resultado['num_imagenes']}")
            if resultado['fallidos'] > 0:
                print(f"  - Fallidas: {resultado['fallidos']}")
        else:
            print(f"{C.R}✗ Error en {indice}: {resultado.get('error', 'Desconocido')}{C.E}")
    
    print(f"\n{C.B}{'='*60}")
    print("PROCESO COMPLETADO")
    print(f"{'='*60}{C.E}\n")
    print(f"{C.G}Las descargas están en: descargas/{C.E}")
    print(f"{C.Y}Cada índice tiene múltiples imágenes del rango de fechas{C.E}")
    print(f"{C.G}Para extraer píxeles, ejecuta: python extraer_pixeles.py{C.E}\n")
    
except Exception as e:
    print(f"\n{C.R}✗ ERROR CRÍTICO: {e}{C.E}")
    print(f"{C.Y}Verifica:{C.E}")
    print(f"  1. Archivo JSON de service account (tesis-*.json) en la carpeta raíz")
    print(f"  2. Shapefile en carpeta shapefiles/")
    print(f"  3. Fechas válidas y rango mínimo de 30 días\n")
    exit(1)
