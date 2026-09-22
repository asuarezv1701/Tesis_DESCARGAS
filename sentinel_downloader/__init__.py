"""
Descargador de Imágenes Satelitales Sentinel-2 (Google Earth Engine)

Sistema para descargar índices de vegetación (NDVI, NDRE, MSAVI, RECI, NDMI)
a partir de la colección Sentinel-2 SR usando Google Earth Engine.
"""

from .gee_downloader import GEEDownloader

__version__ = "3.0.0"
__all__ = ["GEEDownloader"]
