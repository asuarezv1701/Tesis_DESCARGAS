"""
Script Simple de Extracción de Píxeles
Extrae valores de todas las descargas disponibles
"""

import os
import numpy as np
import rasterio
import pandas as pd
import geopandas as gpd
from pathlib import Path
from shapely.geometry import Point

# Colores
class C:
    G = '\033[92m'; Y = '\033[93m'; R = '\033[91m'; B = '\033[94m'; E = '\033[0m'

def extraer_valores_tiff(tiff_path, indice_nombre):
    """Extrae valores de píxeles de un archivo TIFF"""
    with rasterio.open(tiff_path) as src:
        datos = src.read(1)  # Leer primera banda
        transform = src.transform
        crs = src.crs
        
        # Obtener coordenadas de píxeles válidos
        filas, cols = np.where(~np.isnan(datos))
        
        pixeles = []
        for fila, col in zip(filas, cols):
            valor = datos[fila, col]
            if not np.isnan(valor):
                # Convertir índices a coordenadas
                lon, lat = rasterio.transform.xy(transform, fila, col)
                pixeles.append({
                    'longitude': lon,
                    'latitude': lat,
                    indice_nombre: valor
                })
        
        return pixeles, crs

print(f"\n{C.B}{'='*60}")
print("   EXTRACTOR DE PÍXELES - ÍNDICES DE VEGETACIÓN")
print(f"{'='*60}{C.E}\n")

# Buscar descargas disponibles con nueva estructura: descargas/area/indice/
base_dir = Path("descargas")
if not base_dir.exists():
    print(f"{C.R}[ERROR] No hay carpeta de descargas{C.E}")
    exit(1)

# Listar áreas y sus índices con descargas
areas_disponibles = []
for area_dir in base_dir.iterdir():
    if area_dir.is_dir():
        indices_en_area = []
        for indice_dir in area_dir.iterdir():
            if indice_dir.is_dir():
                descargas = [d for d in indice_dir.iterdir() if d.is_dir()]
                if descargas:
                    indices_en_area.append((indice_dir.name, len(descargas)))
        
        if indices_en_area:
            areas_disponibles.append((area_dir.name, indices_en_area))

if not areas_disponibles:
    print(f"{C.R}[ERROR] No hay descargas disponibles para extraer{C.E}")
    exit(1)

print(f"{C.Y}Descargas encontradas:{C.E}")
total_indices = 0
for area, indices in areas_disponibles:
    print(f"  • Área: {area}")
    for indice, count in indices:
        print(f"    - {indice}: {count} carpetas")
        total_indices += 1
print(f"\nTotal: {total_indices} índices en {len(areas_disponibles)} área(s)\n")

confirmar = input(f"{C.Y}¿Extraer píxeles de todas las descargas? (s/n): {C.E}").strip().lower()

if confirmar != 's':
    print(f"{C.Y}[CANCELADO] Extracción cancelada por el usuario{C.E}")
    exit(0)

forzar = input(f"{C.Y}¿Re-extraer también las carpetas que ya tienen valores_pixeles? (s/N): {C.E}").strip().lower() == 's'
if not forzar:
    print(f"{C.G}[OK] Solo se procesarán carpetas nuevas (sin valores_pixeles){C.E}")

print(f"\n{C.B}Iniciando extracción...{C.E}\n")

try:
    total_extraidos = 0
    total_omitidas = 0
    
    for area, indices in areas_disponibles:
        print(f"{C.B}Procesando área: {area}{C.E}")
        
        for indice, count in indices:
            print(f"  {C.Y}Procesando {indice}...{C.E}")
            
            indice_path = base_dir / area / indice
            for descarga_dir in indice_path.iterdir():
                if descarga_dir.is_dir():
                    # Buscar archivo .tiff
                    tiff_files = list(descarga_dir.glob("*.tiff")) + list(descarga_dir.glob("*.tif"))
                    if tiff_files:
                        tiff_file = tiff_files[0]
                        carpeta_valores = descarga_dir / "valores_pixeles"
                        if not forzar and any(carpeta_valores.glob("*.csv")):
                            total_omitidas += 1
                            continue
                        print(f"    Extrayendo: {descarga_dir.name}")
                        
                        try:
                            # Extraer píxeles
                            pixeles, crs = extraer_valores_tiff(str(tiff_file), indice)
                            
                            if pixeles:
                                # Crear carpeta valores_pixeles
                                carpeta_valores = descarga_dir / "valores_pixeles"
                                carpeta_valores.mkdir(exist_ok=True)
                                
                                # Guardar CSV
                                df = pd.DataFrame(pixeles)
                                csv_path = carpeta_valores / f"pixeles_{indice}_{descarga_dir.name}.csv"
                                df.to_csv(csv_path, index=False)
                                
                                # Guardar Shapefile
                                geometry = [Point(p['longitude'], p['latitude']) for p in pixeles]
                                gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=crs)
                                shp_path = carpeta_valores / f"pixeles_{indice}_{descarga_dir.name}.shp"
                                gdf.to_file(shp_path)
                                
                                print(f"    {C.G}[OK] {len(pixeles)} píxeles extraídos{C.E}")
                                total_extraidos += len(pixeles)
                            else:
                                print(f"    {C.Y}[AVISO] No se encontraron píxeles válidos{C.E}")
                                
                        except Exception as e:
                            print(f"    {C.R}[ERROR] Error: {e}{C.E}")
    
    print(f"\n{C.B}{'='*60}")
    print(f"EXTRACCIÓN COMPLETADA")
    print(f"{'='*60}{C.E}")
    print(f"{C.G}Total píxeles extraídos: {total_extraidos}{C.E}")
    print(f"{C.Y}Carpetas omitidas (ya extraídas): {total_omitidas}{C.E}")
    print(f"{C.Y}Los archivos CSV y Shapefile están en cada carpeta de descarga{C.E}\n")
    
except Exception as e:
    print(f"\n{C.R}[ERROR] ERROR: {e}{C.E}\n")
    exit(1)
