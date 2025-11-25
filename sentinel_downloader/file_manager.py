"""
Utilidades de E/S de archivos para guardar y gestionar archivos GeoTIFF.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from sentinelhub import BBox, CRS

from .config import ProcessingConfig


class FileManager:
    """Maneja operaciones de archivos para datos satelitales"""
    
    def __init__(self, processing_config: ProcessingConfig):
        self.processing_config = processing_config
        self.logger = logging.getLogger(__name__)
        
    def create_output_directory(self, output_dir: str) -> bool:
        """Crea el directorio de salida si no existe"""
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Directorio de salida listo: {output_dir}")
            return True
        except Exception as e:
            self.logger.error(f"Falló la creación del directorio {output_dir}: {str(e)}")
            return False
            
    def generate_filename(self, start_date: str, end_date: str, prefix: str = "indices") -> str:
        """Genera nombre de archivo estandarizado"""
        # Limpiar fechas para nombre de archivo
        start_clean = start_date.replace('-', '')
        end_clean = end_date.replace('-', '')
        return f"{prefix}_{start_clean}_a_{end_clean}.tiff"
        
    def validate_output_path(self, output_path: str) -> bool:
        """Valida la ruta de salida"""
        path = Path(output_path)
        
        # Verificar si el directorio existe o puede crearse
        if not path.parent.exists():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.logger.error(f"No se puede crear el directorio de salida: {str(e)}")
                return False
                
        # Verificar si el archivo ya existe
        if path.exists():
            self.logger.warning(f"El archivo de salida ya existe: {output_path}")
            
        return True
        
    def save_geotiff(
        self,
        data: List[np.ndarray],
        bbox: BBox,
        output_path: str,
        band_names: List[str],
        band_descriptions: Optional[List[str]] = None
    ) -> bool:
        """
        Guarda datos como GeoTIFF con metadatos completos
        
        Args:
            data: Lista de arrays numpy 2D (uno por banda)
            bbox: Caja delimitadora de los datos
            output_path: Ruta del archivo de salida
            band_names: Nombres para cada banda
            band_descriptions: Descripciones detalladas opcionales
            
        Returns:
            True si es exitoso, False en caso contrario
        """
        try:
            if not data or len(data) == 0:
                self.logger.error("No hay datos para guardar")
                return False
                
            if not self.validate_output_path(output_path):
                return False
                
            # Obtener dimensiones de la primera banda
            height, width = data[0].shape
            self.logger.info(f"Guardando GeoTIFF: {width}x{height} píxeles, {len(data)} bandas")
            
            # Crear geotransformación
            transform = from_bounds(*bbox, width, height)
            
            # Configurar perfil del raster
            profile = {
                'driver': self.processing_config.output_format,
                'height': height,
                'width': width,
                'count': len(data),
                'dtype': self.processing_config.data_type,
                'crs': CRS.WGS84.pyproj_crs(),
                'transform': transform,
                'compress': self.processing_config.compression,
                'tiled': True,  # Habilitar mosaicos para mejor rendimiento
                'blockxsize': 512,
                'blockysize': 512
            }
            
            # Agregar manejo de valores NODATA
            profile['nodata'] = -9999.0
            
            # Escribir el archivo
            with rasterio.open(output_path, 'w', **profile) as dst:
                for i, band_data in enumerate(data, 1):
                    # Manejar posibles valores NaN
                    clean_data = band_data.astype(profile['dtype'])
                    clean_data = np.where(np.isnan(clean_data), profile['nodata'], clean_data)
                    
                    dst.write(clean_data, i)
                    
                    # Establecer descripción de banda
                    if i <= len(band_names):
                        dst.set_band_description(i, band_names[i-1])
                        
                # Agregar metadatos
                metadata = {
                    'creation_date': str(np.datetime64('now')),
                    'software': 'Descargador Sentinel',
                    'resolution_meters': str(self.processing_config.resolution),
                    'compression': self.processing_config.compression
                }
                
                if band_descriptions:
                    for i, desc in enumerate(band_descriptions, 1):
                        metadata[f'band_{i}_description'] = desc
                        
                dst.update_tags(**metadata)
                
            # Verificar que el archivo fue creado exitosamente
            if Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                self.logger.info(f"GeoTIFF guardado exitosamente:")
                self.logger.info(f"  - Archivo: {output_path}")
                self.logger.info(f"  - Tamaño: {file_size / (1024*1024):.2f} MB")
                self.logger.info(f"  - Bandas: {len(band_names)}")
                
                for i, name in enumerate(band_names, 1):
                    self.logger.info(f"    {i}. {name}")
                    
                return True
            else:
                self.logger.error("El archivo no fue creado exitosamente")
                return False
                
        except Exception as e:
            self.logger.error(f"Error guardando GeoTIFF {output_path}: {str(e)}")
            return False
            
    def limpiar_archivos_temporales(self, directorio_temp: str):
        """Limpia archivos temporales del directorio especificado"""
        try:
            ruta_temp = Path(directorio_temp)
            if ruta_temp.exists() and ruta_temp.is_dir():
                # Buscar y eliminar archivos .tmp
                archivos_tmp = list(ruta_temp.glob("*.tmp"))
                for archivo in archivos_tmp:
                    archivo.unlink()
                self.logger.debug(f"Archivos temporales limpiados en {directorio_temp}")
        except Exception as error:
            self.logger.warning(f"Error limpiando archivos temporales: {str(error)}")
            
    def obtener_info_archivo(self, ruta_archivo: str) -> dict:
        """Obtiene información detallada sobre un archivo GeoTIFF existente"""
        informacion_archivo = {}
        try:
            with rasterio.open(ruta_archivo) as fuente_datos:
                # Recopilar información básica del archivo
                informacion_archivo = {
                    'controlador': fuente_datos.driver,
                    'tipo_dato': fuente_datos.dtypes[0],
                    'ancho': fuente_datos.width,
                    'alto': fuente_datos.height,
                    'num_bandas': fuente_datos.count,
                    'sistema_coordenadas': str(fuente_datos.crs),
                    'transformacion': fuente_datos.transform,
                    'limites': fuente_datos.bounds,
                    'valor_nulo': fuente_datos.nodata,
                    'compresion': fuente_datos.compression
                }
                
                # Obtener descripciones de bandas
                descripciones_bandas = []
                for i in range(fuente_datos.count):
                    desc = fuente_datos.descriptions[i] if fuente_datos.descriptions[i] else f"Banda_{i+1}"
                    descripciones_bandas.append(desc)
                    
                informacion_archivo['descripciones_bandas'] = descripciones_bandas
                
                return informacion_archivo
                
        except Exception as error_lectura:
            self.logger.error(f"Error leyendo información del archivo {ruta_archivo}: {str(error_lectura)}")
            return informacion_archivo