"""
Cliente API para Sentinel Hub con manejo robusto de errores y lógica de reintentos.
"""

import time
import logging
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from sentinelhub import (
    SHConfig,
    SentinelHubRequest,
    DataCollection,
    MimeType,
    BBox,
    CRS,
    bbox_to_dimensions,
    Geometry
)

from .config import APIConfig, ProcessingConfig
from .indices import VegetationIndicesProcessor


class SentinelHubAPIError(Exception):
    """Excepción personalizada para errores de la API de Sentinel Hub"""
    pass


class RateLimitError(SentinelHubAPIError):
    """Excepción para errores de límite de velocidad"""
    pass


class APIClient:
    """
    Cliente robusto de API Sentinel Hub con manejo de errores y lógica de reintentos
    """
    
    def __init__(self, api_config: APIConfig, processing_config: ProcessingConfig):
        self.api_config = api_config
        self.processing_config = processing_config
        self.logger = logging.getLogger(__name__)
        
        # Configurar Sentinel Hub
        self.config = SHConfig()
        self.config.sh_client_id = api_config.client_id
        self.config.sh_client_secret = api_config.client_secret
        
        # Inicializar procesadores
        self.indices_processor = VegetationIndicesProcessor()
        
        # Configurar sesión de requests con lógica de reintentos
        self.session = self._create_session()
        
        # Limitación de velocidad
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Segundos mínimos entre requests
        
    def _create_session(self) -> requests.Session:
        """Crea sesión de requests con estrategia de reintentos"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.api_config.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=self.api_config.retry_delay
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
        
    def _validate_credentials(self) -> bool:
        """Valida las credenciales de la API"""
        try:
            # Validación simple creando una petición mínima
            # Esto no envía datos realmente, solo valida la configuración
            if not self.config.sh_client_id or not self.config.sh_client_secret:
                self.logger.error("Las credenciales de API están vacías")
                return False
                
            self.logger.info("Credenciales de API validadas")
            return True
            
        except Exception as e:
            self.logger.error(f"Fallo en validación de credenciales: {str(e)}")
            return False
            
    def _apply_rate_limit(self):
        """Aplica limitación de velocidad entre peticiones"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            self.logger.debug(f"Limitando velocidad: esperando {sleep_time:.2f} segundos")
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
        
    def _validate_date_range(self, start_date: str, end_date: str) -> bool:
        """Valida el rango de fechas"""
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            
            if start_dt >= end_dt:
                self.logger.error(f"Rango de fechas inválido: {start_date} >= {end_date}")
                return False
                
            # Verificar si el rango de fechas es demasiado grande
            if (end_dt - start_dt).days > 90:
                self.logger.warning(f"Rango de fechas amplio: {(end_dt - start_dt).days} días")
                
            # Verificar que las fechas no sean muy antiguas
            sentinel2_start = datetime(2015, 6, 23)  # Fecha de lanzamiento Sentinel-2A
            if start_dt < sentinel2_start:
                self.logger.error(f"Fecha de inicio {start_date} es anterior a disponibilidad de Sentinel-2")
                return False
                
            return True
            
        except ValueError as e:
            self.logger.error(f"Formato de fecha inválido: {str(e)}")
            return False
            
    def download_indices(
        self,
        geometry: Geometry,
        bbox: BBox,
        start_date: str,
        end_date: str
    ) -> Optional[List]:
        """
        Descarga índices de vegetación para geometría y rango de fechas especificados
        
        Args:
            geometry: Geometría del área
            bbox: Caja delimitadora
            start_date: Fecha de inicio (YYYY-MM-DD)
            end_date: Fecha de fin (YYYY-MM-DD)
            
        Returns:
            Lista de arrays numpy o None si falla
        """
        try:
            # Validar entradas
            if not self._validate_credentials():
                return None
                
            if not self._validate_date_range(start_date, end_date):
                return None
                
            # Aplicar limitación de velocidad
            self._apply_rate_limit()
            
            # Calcular dimensiones
            size = bbox_to_dimensions(bbox, resolution=self.processing_config.resolution)
            
            self.logger.info(f"Descargando datos:")
            self.logger.info(f"  - Rango de fechas: {start_date} a {end_date}")
            self.logger.info(f"  - Resolución: {self.processing_config.resolution}m")
            self.logger.info(f"  - Tamaño de imagen: {size}")
            self.logger.info(f"  - Bbox: {bbox}")
            
            # Create request
            request = SentinelHubRequest(
                evalscript=self.indices_processor.get_evalscript(),
                input_data=[
                    SentinelHubRequest.input_data(
                        data_collection=DataCollection.SENTINEL2_L2A,
                        time_interval=(start_date, end_date),
                        maxcc=self.processing_config.max_cloud_coverage
                    )
                ],
                responses=[
                    SentinelHubRequest.output_response('default', MimeType.TIFF)
                ],
                geometry=geometry,
                bbox=bbox,
                size=size,
                config=self.config
            )
            
            # Ejecutar petición con timeout
            self.logger.info("Ejecutando petición a la API...")
            start_time = time.time()
            
            data = request.get_data()
            
            execution_time = time.time() - start_time
            self.logger.info(f"Petición completada en {execution_time:.2f} segundos")
            
            if not data or len(data) == 0:
                self.logger.error("No se recibieron datos de la API")
                return None
            
            # Debug: imprimir información sobre los datos recibidos
            self.logger.info(f"DEBUG: Tipo de datos recibidos: {type(data)}")
            self.logger.info(f"DEBUG: Longitud de datos: {len(data)}")
            if len(data) > 0:
                self.logger.info(f"DEBUG: Tipo del primer elemento: {type(data[0])}")
                self.logger.info(f"DEBUG: Shape del primer elemento: {data[0].shape if hasattr(data[0], 'shape') else 'N/A'}")
            
            # Los datos vienen como [array(H, W, Bands)], necesitamos convertir a lista de bandas
            if len(data) == 1 and hasattr(data[0], 'shape') and len(data[0].shape) == 3:
                # Desempaquetar: de (H, W, 6) a lista de 6 arrays (H, W)
                import numpy as np
                image_data = data[0]  # Shape: (H, W, 6)
                num_bands = image_data.shape[2]
                # Separar en lista de bandas
                data = [image_data[:, :, i] for i in range(num_bands)]
                self.logger.info(f"Datos convertidos: {len(data)} bandas de shape {data[0].shape}")
                
            # Validar datos de salida
            if not self.indices_processor.validate_output_data(data):
                self.logger.error("Falló la validación de datos")
                return None
                
            self.logger.info(f"Se descargaron exitosamente {len(data)} bandas")
            return data
            
        except requests.exceptions.Timeout:
            self.logger.error("La petición ha superado el tiempo límite")
            return None
            
        except requests.exceptions.ConnectionError:
            self.logger.error("Error de conexión")
            return None
            
        except Exception as e:
            if "rate limit" in str(e).lower():
                self.logger.error(f"Límite de velocidad excedido: {str(e)}")
                raise RateLimitError(str(e))
            else:
                self.logger.error(f"Falló la petición a la API: {str(e)}")
                return None
                
    def test_connection(self) -> bool:
        """Prueba la conexión y credenciales de la API"""
        try:
            self.logger.info("Probando conexión de API...")
            
            if not self._validate_credentials():
                return False
                
            # Crear petición de prueba mínima (área pequeña, fecha reciente)
            from shapely.geometry import Point
            import geopandas as gpd
            
            # Área de prueba pequeña alrededor de Londres
            test_point = Point(-0.1276, 51.5074)  # Coordenadas de Londres
            test_gdf = gpd.GeoDataFrame([1], geometry=[test_point.buffer(0.001)], crs='EPSG:4326')
            
            test_geometry = Geometry(test_gdf.geometry.iloc[0].__geo_interface__, crs=CRS.WGS84)
            test_bbox = BBox(test_geometry.geometry.bounds, crs=CRS.WGS84)
            
            # Probar con un rango de fechas reciente pequeño
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            result = self.download_indices(test_geometry, test_bbox, start_date, end_date)
            
            if result is not None:
                self.logger.info("Prueba de conexión de API exitosa")
                return True
            else:
                self.logger.error("Falló la prueba de conexión de API")
                return False
                
        except Exception as e:
            self.logger.error(f"Falló la prueba de conexión: {str(e)}")
            return False