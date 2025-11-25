"""
Módulo de configuración para el descargador de imágenes satelitales Sentinel-2.
Maneja credenciales de API, rutas y ajustes de la aplicación.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


@dataclass
class APIConfig:
    """Configuración para la API de Sentinel Hub"""
    client_id: str
    client_secret: str
    timeout: int = 300  # tiempo de espera por defecto: 5 minutos
    max_retries: int = 3
    retry_delay: int = 5  # segundos entre reintentos


@dataclass
class ProcessingConfig:
    """Configuración para procesamiento de imágenes"""
    resolution: int = 10  # metros
    max_cloud_coverage: float = 0.3  # 30% cobertura nubosa máxima
    output_format: str = 'GTiff'
    compression: str = 'lzw'
    data_type: str = 'float32'


class ConfigurationManager:
    """Administra la configuración y validación de la aplicación"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_path()
        self._setup_logging()
        
    def _get_default_config_path(self) -> str:
        """Obtiene la ruta del archivo de configuración por defecto"""
        return os.path.join(os.path.expanduser("~"), ".sentinel_config")
        
    def _setup_logging(self):
        """Configura el sistema de logging estructurado"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "sentinel_downloader.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_api_config(self) -> APIConfig:
        """Carga configuración de API desde variables de entorno o archivo de config"""
        client_id = os.getenv('SENTINEL_CLIENT_ID')
        client_secret = os.getenv('SENTINEL_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            self.logger.error("Faltan credenciales de API. Configure las variables SENTINEL_CLIENT_ID y SENTINEL_CLIENT_SECRET")
            raise ValueError("Credenciales de API faltantes")
            
        return APIConfig(
            client_id=client_id,
            client_secret=client_secret,
            timeout=int(os.getenv('SENTINEL_TIMEOUT', '300')),
            max_retries=int(os.getenv('SENTINEL_MAX_RETRIES', '3')),
            retry_delay=int(os.getenv('SENTINEL_RETRY_DELAY', '5'))
        )
        
    def get_processing_config(self) -> ProcessingConfig:
        """Obtiene la configuración de procesamiento de imágenes"""
        return ProcessingConfig(
            resolution=int(os.getenv('SENTINEL_RESOLUTION', '10')),
            max_cloud_coverage=float(os.getenv('SENTINEL_MAX_CLOUD', '0.3')),
            output_format=os.getenv('SENTINEL_OUTPUT_FORMAT', 'GTiff'),
            compression=os.getenv('SENTINEL_COMPRESSION', 'lzw'),
            data_type=os.getenv('SENTINEL_DATA_TYPE', 'float32')
        )


# Instancia global de configuración
config_manager = ConfigurationManager()