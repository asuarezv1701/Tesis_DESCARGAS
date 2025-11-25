"""
Utilidades de procesamiento geométrico para manejo de shapefiles y datos espaciales.
"""

import logging
from pathlib import Path
from typing import Tuple, Optional
import geopandas as gpd
from sentinelhub import Geometry, BBox, CRS


class GeometryProcessor:
    """Maneja el procesamiento y validación de datos espaciales"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def validate_shapefile(self, shapefile_path: str) -> bool:
        """Valida que el shapefile existe y tiene el formato correcto"""
        path = Path(shapefile_path)
        
        if not path.exists():
            self.logger.error(f"Shapefile no encontrado: {shapefile_path}")
            return False
            
        if not path.suffix.lower() == '.shp':
            self.logger.error(f"El archivo no es un shapefile: {shapefile_path}")
            return False
            
        # Verificar componentes requeridos del shapefile
        required_files = ['.shp', '.shx', '.dbf']
        for ext in required_files:
            if not path.with_suffix(ext).exists():
                self.logger.error(f"Falta componente del shapefile: {path.with_suffix(ext)}")
                return False
                
        return True
        
    def load_shapefile(self, shapefile_path: str) -> Tuple[Optional[Geometry], Optional[BBox], Optional[gpd.GeoDataFrame]]:
        """
        Carga shapefile y retorna geometry, bbox, y geodataframe
        
        Returns:
            Tupla de (Geometry, BBox, GeoDataFrame) o (None, None, None) si falla
        """
        try:
            if not self.validate_shapefile(shapefile_path):
                return None, None, None
                
            self.logger.info(f"Cargando shapefile: {shapefile_path}")
            gdf = gpd.read_file(shapefile_path)
            
            if gdf.empty:
                self.logger.error("El shapefile no contiene elementos")
                return None, None, None
                
            # Verificar y transformar CRS si es necesario
            original_crs = gdf.crs
            if gdf.crs != CRS.WGS84:
                self.logger.info(f"Transformando CRS de {original_crs} a WGS84")
                gdf = gdf.to_crs(CRS.WGS84.pyproj_crs())
                
            # Obtener primera geometría (asumiendo un solo elemento o usando el primero)
            if len(gdf) > 1:
                self.logger.warning(f"El shapefile contiene {len(gdf)} elementos. Usando el primero.")
                
            first_geometry = gdf.geometry.iloc[0]
            
            # Validar geometría
            if not first_geometry.is_valid:
                self.logger.error("La geometría no es válida")
                return None, None, None
                
            # Create Sentinel Hub geometry and bbox
            geometry = Geometry(first_geometry.__geo_interface__, crs=CRS.WGS84)
            bbox = BBox(geometry.geometry.bounds, crs=CRS.WGS84)
            
            # Registrar información de la geometría
            bounds = geometry.geometry.bounds
            area = first_geometry.area
            self.logger.info(f"Geometría cargada exitosamente:")
            self.logger.info(f"  - Límites: {bounds}")
            self.logger.info(f"  - Área: {area:.6f} grados cuadrados")
            self.logger.info(f"  - CRS original: {original_crs}")
            
            return geometry, bbox, gdf
            
        except Exception as e:
            self.logger.error(f"Error cargando shapefile {shapefile_path}: {str(e)}")
            return None, None, None
            
    def calculate_area_km2(self, gdf: gpd.GeoDataFrame) -> float:
        """Calcula el área en kilómetros cuadrados"""
        try:
            # Transformar a CRS proyectado para cálculo preciso de área
            # Usando Web Mercator para cálculos globales aproximados
            gdf_projected = gdf.to_crs('EPSG:3857')
            area_m2 = gdf_projected.geometry.iloc[0].area
            area_km2 = area_m2 / 1_000_000  # Convertir a km²
            
            self.logger.info(f"Área: {area_km2:.2f} km²")
            return area_km2
            
        except Exception as e:
            self.logger.error(f"Error calculando área: {str(e)}")
            return 0.0
            
    def validate_geometry_size(self, geometry: Geometry, max_area_km2: float = 1000.0) -> bool:
        """Valida que la geometría no sea demasiado grande para procesar"""
        try:
            # Crear GeoDataFrame temporal para cálculo de área
            import shapely.geometry
            geom = shapely.geometry.shape(geometry.geometry)
            gdf_temp = gpd.GeoDataFrame([1], geometry=[geom], crs=CRS.WGS84.pyproj_crs())
            
            area_km2 = self.calculate_area_km2(gdf_temp)
            
            if area_km2 > max_area_km2:
                self.logger.error(f"Geometría demasiado grande: {area_km2:.2f} km² > {max_area_km2} km²")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error validando tamaño de geometría: {str(e)}")
            return False