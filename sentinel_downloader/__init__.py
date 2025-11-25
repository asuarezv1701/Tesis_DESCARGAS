"""
Descargador de Imágenes Satelitales Sentinel-2
Herramienta robusta para descarga de índices de vegetación desde la API de Sentinel Hub
Desarrollado específicamente para el contexto mexicano con optimizaciones regionales
"""

from .config import ConfigurationManager
from .downloader import DescargadorSatelital
from .geometry import GeometryProcessor
from .api_client import APIClient
from .file_manager import FileManager
from .indices import VegetationIndicesProcessor
from .utilidades_mx import UtileriasDescarga
from .config_avanzada import GestorConfiguracionAvanzada

__version__ = "2.1.0-mx"
__author__ = "Equipo de Procesamiento de Datos Satelitales México"
__descripcion__ = "Sistema avanzado de descarga satelital optimizado para territorio mexicano"

# Componentes principales del sistema
__all__ = [
    'ConfigurationManager',
    'DescargadorSatelital', 
    'GeometryProcessor',
    'APIClient',
    'FileManager',
    'VegetationIndicesProcessor',
    'UtileriasDescarga',
    'GestorConfiguracionAvanzada'
]

# Compatibilidad con versión anterior
SatelliteDownloader = DescargadorSatelital