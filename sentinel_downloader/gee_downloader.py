"""
Módulo de descarga usando Google Earth Engine
Descarga múltiples imágenes Sentinel-2 con índices de vegetación
"""

import ee
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import geopandas as gpd
from shapely.geometry import mapping
import requests
import numpy as np
import rasterio
from rasterio.transform import from_bounds


class GEEDownloader:
    """Descargador de imágenes Sentinel-2 usando Google Earth Engine"""
    
    # Fórmulas de índices de vegetación
    INDICES = {
        'NDVI': '(NIR - RED) / (NIR + RED)',
        'NDRE': '(NIR - RED_EDGE) / (NIR + RED_EDGE)',
        'MSAVI': '(2 * NIR + 1 - sqrt(pow(2 * NIR + 1, 2) - 8 * (NIR - RED))) / 2',
        'RECI': '(NIR / RED_EDGE) - 1',
        'NDMI': '(NIR - SWIR1) / (NIR + SWIR1)'
    }
    
    # Mapeo de bandas Sentinel-2
    BANDAS = {
        'RED': 'B4',
        'NIR': 'B8',
        'RED_EDGE': 'B5',
        'SWIR1': 'B11'
    }
    
    def __init__(self, output_dir: str = "descargas", service_account_json: str = None):
        """
        Inicializa el descargador de GEE
        
        Args:
            output_dir: Directorio base para guardar descargas
            service_account_json: Ruta al archivo JSON de service account
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        
        # Inicializar GEE con service account
        try:
            # Buscar archivo JSON si no se especificó
            if service_account_json is None:
                json_files = list(Path('.').glob('tesis-*.json'))
                if json_files:
                    service_account_json = str(json_files[0])
                    self.logger.info(f"Usando service account: {json_files[0].name}")
            
            if service_account_json and Path(service_account_json).exists():
                # Autenticar con service account
                credentials = ee.ServiceAccountCredentials(
                    email=None,  # Se lee del JSON
                    key_file=service_account_json
                )
                ee.Initialize(credentials)
                self.logger.info("✓ Google Earth Engine inicializado con service account")
            else:
                # Intentar inicialización normal
                ee.Initialize()
                self.logger.info("✓ Google Earth Engine inicializado")
                
        except Exception as e:
            self.logger.error(f"✗ Error al inicializar GEE: {e}")
            self.logger.info("Coloca el archivo tesis-*.json en la carpeta raíz")
            raise
    
    def leer_shapefile(self, shapefile_path: str) -> ee.Geometry:
        """
        Lee un shapefile y lo convierte a geometría de GEE
        
        Args:
            shapefile_path: Ruta al archivo shapefile
            
        Returns:
            Geometría de Earth Engine
        """
        gdf = gpd.read_file(shapefile_path)
        
        # Convertir a WGS84 si no lo está
        if gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
        
        # Obtener geometría
        geom = gdf.geometry.iloc[0]
        geom_dict = mapping(geom)
        
        # Crear geometría de EE
        ee_geom = ee.Geometry(geom_dict)
        
        return ee_geom
    
    def obtener_imagenes(self, 
                        geometria: ee.Geometry,
                        fecha_inicio: str,
                        fecha_fin: str,
                        max_cloud: float = 30) -> ee.ImageCollection:
        """
        Obtiene colección de imágenes Sentinel-2
        
        Args:
            geometria: Área de interés
            fecha_inicio: Fecha inicio (YYYY-MM-DD)
            fecha_fin: Fecha fin (YYYY-MM-DD)
            max_cloud: Máximo % de nubes permitido
            
        Returns:
            Colección de imágenes filtradas
        """
        coleccion = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                    .filterBounds(geometria)
                    .filterDate(fecha_inicio, fecha_fin)
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', max_cloud)))
        
        num_imagenes = coleccion.size().getInfo()
        self.logger.info(f"Encontradas {num_imagenes} imágenes en el rango de fechas")
        
        return coleccion
    
    def calcular_indice(self, imagen: ee.Image, indice: str) -> ee.Image:
        """
        Calcula un índice de vegetación
        
        Args:
            imagen: Imagen Sentinel-2
            indice: Nombre del índice (NDVI, NDRE, MSAVI, RECI, NDMI)
            
        Returns:
            Imagen con el índice calculado
        """
        # Mapear bandas
        red = imagen.select('B4')
        nir = imagen.select('B8')
        red_edge = imagen.select('B5')
        swir1 = imagen.select('B11')
        
        if indice == 'NDVI':
            return nir.subtract(red).divide(nir.add(red)).rename('NDVI')
        
        elif indice == 'NDRE':
            return nir.subtract(red_edge).divide(nir.add(red_edge)).rename('NDRE')
        
        elif indice == 'MSAVI':
            # MSAVI = (2 * NIR + 1 - sqrt((2 * NIR + 1)^2 - 8 * (NIR - RED))) / 2
            nir2 = nir.multiply(2)
            raiz = nir2.add(1).pow(2).subtract(nir.subtract(red).multiply(8)).sqrt()
            return nir2.add(1).subtract(raiz).divide(2).rename('MSAVI')
        
        elif indice == 'RECI':
            return nir.divide(red_edge).subtract(1).rename('RECI')
        
        elif indice == 'NDMI':
            return nir.subtract(swir1).divide(nir.add(swir1)).rename('NDMI')
        
        else:
            raise ValueError(f"Índice no soportado: {indice}")
    
    def descargar_imagen(self,
                        imagen: ee.Image,
                        geometria: ee.Geometry,
                        indice: str,
                        fecha: str,
                        nombre_area: str = "area") -> Dict:
        """
        Descarga una imagen con el índice calculado
        
        Args:
            imagen: Imagen de Earth Engine
            geometria: Área de interés
            indice: Índice a calcular
            fecha: Fecha de la imagen
            nombre_area: Nombre del área
            
        Returns:
            Diccionario con información de la descarga
        """
        # Crear carpeta de salida
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        carpeta_indice = self.output_dir / indice
        carpeta_descarga = carpeta_indice / f"{nombre_area}_{fecha}_{timestamp}"
        carpeta_descarga.mkdir(parents=True, exist_ok=True)
        
        # Calcular índice
        indice_img = self.calcular_indice(imagen, indice)
        
        # Recortar a geometría
        indice_recortado = indice_img.clip(geometria)
        
        # Obtener URL de descarga
        bounds = geometria.bounds().getInfo()['coordinates'][0]
        
        # Calcular región para exportación
        region = geometria.bounds()
        
        try:
            # Obtener URL de descarga
            url = indice_recortado.getDownloadURL({
                'scale': 10,  # 10 metros de resolución
                'region': region,
                'format': 'GEO_TIFF'
            })
            
            # Descargar archivo
            archivo_tiff = carpeta_descarga / f"{nombre_area}_{fecha}_{indice}.tiff"
            
            self.logger.info(f"Descargando {indice} de {fecha}...")
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            with open(archivo_tiff, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"✓ Descargado: {archivo_tiff.name}")
            
            return {
                'exito': True,
                'archivo': str(archivo_tiff),
                'carpeta': str(carpeta_descarga),
                'indice': indice,
                'fecha': fecha
            }
            
        except Exception as e:
            self.logger.error(f"Error al descargar {indice} de {fecha}: {e}")
            return {
                'exito': False,
                'error': str(e),
                'indice': indice,
                'fecha': fecha
            }
    
    def descargar_indice(self,
                        shapefile_path: str,
                        indice: str,
                        fecha_inicio: str,
                        fecha_fin: str,
                        nombre_area: str = "area",
                        max_cloud: float = 30) -> Dict:
        """
        Descarga todas las imágenes de un índice en un rango de fechas
        
        Args:
            shapefile_path: Ruta al shapefile del área
            indice: Índice a descargar
            fecha_inicio: Fecha inicio (YYYY-MM-DD)
            fecha_fin: Fecha fin (YYYY-MM-DD)
            nombre_area: Nombre del área
            max_cloud: Máximo % de nubes
            
        Returns:
            Diccionario con resultados
        """
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Descargando {indice}: {fecha_inicio} a {fecha_fin}")
        self.logger.info(f"{'='*60}")
        
        try:
            # Leer geometría
            geometria = self.leer_shapefile(shapefile_path)
            
            # Obtener imágenes
            coleccion = self.obtener_imagenes(geometria, fecha_inicio, fecha_fin, max_cloud)
            
            # Obtener lista de imágenes
            imagenes_info = coleccion.getInfo()
            num_imagenes = len(imagenes_info['features'])
            
            if num_imagenes == 0:
                self.logger.warning(f"No se encontraron imágenes para {indice}")
                return {
                    'exito': False,
                    'error': 'No hay imágenes disponibles',
                    'num_imagenes': 0
                }
            
            # Descargar cada imagen
            resultados = []
            for i, img_info in enumerate(imagenes_info['features'], 1):
                img_id = img_info['id']
                fecha_img = img_info['properties']['system:time_start']
                fecha_str = datetime.fromtimestamp(fecha_img / 1000).strftime('%Y%m%d')
                
                self.logger.info(f"[{i}/{num_imagenes}] Procesando imagen {fecha_str}")
                
                imagen = ee.Image(img_id)
                resultado = self.descargar_imagen(imagen, geometria, indice, fecha_str, nombre_area)
                resultados.append(resultado)
            
            # Resumen
            exitosos = sum(1 for r in resultados if r['exito'])
            
            return {
                'exito': True,
                'indice': indice,
                'num_imagenes': num_imagenes,
                'exitosos': exitosos,
                'fallidos': num_imagenes - exitosos,
                'resultados': resultados
            }
            
        except Exception as e:
            self.logger.error(f"Error en descarga de {indice}: {e}")
            return {
                'exito': False,
                'error': str(e),
                'indice': indice
            }
