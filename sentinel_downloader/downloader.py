"""
Módulo principal de descarga que orquesta el proceso de descarga de datos satelitales.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

from .config import ConfigurationManager
from .geometry import GeometryProcessor
from .api_client import APIClient, RateLimitError
from .file_manager import FileManager
from .indices import VegetationIndicesProcessor


class DescargadorSatelital:
    """Clase principal para descarga de imágenes satelitales e índices de vegetación"""
    
    def __init__(self, gestor_config: ConfigurationManager = None):
        # Inicializar gestor de configuración
        self.gestor_config = gestor_config if gestor_config else ConfigurationManager()
        self.registro_eventos = logging.getLogger(__name__)
        self.logger = self.registro_eventos  # Alias for compatibility
        
        # Cargar configuraciones del sistema
        self.config_api = self.gestor_config.load_api_config()
        self.config_procesamiento = self.gestor_config.get_processing_config()
        
        # Inicializar componentes del sistema
        self.procesador_geometria = GeometryProcessor()
        self.cliente_api = APIClient(self.config_api, self.config_procesamiento)
        self.gestor_archivos = FileManager(self.config_procesamiento)
        self.procesador_indices = VegetationIndicesProcessor()
        
    def probar_configuracion(self) -> bool:
        """Prueba la configuración completa antes de ejecutar descargas en lote"""
        self.registro_eventos.info("Probando configuración del descargador...")
        
        resultado_prueba = False
        try:
            # Probar conexión con la API
            conexion_exitosa = self.cliente_api.test_connection()
            if not conexion_exitosa:
                self.registro_eventos.error("Falló la prueba de conexión con la API")
                return resultado_prueba
                
            self.registro_eventos.info("Prueba de configuración completada exitosamente")
            resultado_prueba = True
            return resultado_prueba
            
        except Exception as error_prueba:
            self.registro_eventos.error(f"Falló la prueba de configuración: {str(error_prueba)}")
            return resultado_prueba
            
    def descargar_periodo_individual(
        self,
        ruta_shapefile: str,
        fecha_inicio: str,
        fecha_fin: str,
        directorio_salida: str
    ) -> Optional[str]:
        """
        Descarga índices de vegetación para un período de tiempo específico
        
        Args:
            ruta_shapefile: Ruta al shapefile que define el área de interés
            fecha_inicio: Fecha de inicio (YYYY-MM-DD)
            fecha_fin: Fecha de fin (YYYY-MM-DD)
            directorio_salida: Directorio de salida
            
        Returns:
            Ruta al archivo guardado o None si falla
        """
        archivo_resultado = None
        try:
            self.registro_eventos.info(f"Iniciando descarga para el período {fecha_inicio} a {fecha_fin}")
            
            # Cargar y validar la geometría del shapefile
            geometria, caja_delimitadora, geodataframe = self.procesador_geometria.load_shapefile(ruta_shapefile)
            if geometria is None:
                self.registro_eventos.error("No fue posible cargar el shapefile")
                return archivo_resultado
                
            # Validar que el tamaño de la geometría sea procesable
            geometria_valida = self.procesador_geometria.validate_geometry_size(geometria)
            if not geometria_valida:
                self.registro_eventos.error("La geometría es demasiado grande para procesamiento")
                return archivo_resultado
                
            # Crear directorio de salida para los archivos
            directorio_creado = self.gestor_archivos.create_output_directory(directorio_salida)
            if not directorio_creado:
                return archivo_resultado
                
            # Descargar datos satelitales de la API
            datos_descargados = self.cliente_api.download_indices(geometria, caja_delimitadora, fecha_inicio, fecha_fin)
            if datos_descargados is None:
                self.registro_eventos.error("No fue posible descargar los datos")
                return archivo_resultado
                
            # Preparar guardado del archivo
            nombre_archivo = self.gestor_archivos.generate_filename(fecha_inicio, fecha_fin)
            ruta_completa_salida = os.path.join(directorio_salida, nombre_archivo)
            
            nombres_bandas = self.procesador_indices.get_band_names()
            descripciones_bandas = self.procesador_indices.get_band_descriptions()
            
            # Guardar como archivo GeoTIFF
            guardado_exitoso = self.gestor_archivos.save_geotiff(
                datos_descargados, caja_delimitadora, ruta_completa_salida, nombres_bandas, descripciones_bandas
            )
            
            if guardado_exitoso:
                self.registro_eventos.info(f"Archivo guardado exitosamente: {ruta_completa_salida}")
                archivo_resultado = ruta_completa_salida
            else:
                self.registro_eventos.error("No fue posible guardar el archivo GeoTIFF")
                
            return archivo_resultado
                
        except RateLimitError:
            self.logger.error("Rate limit exceeded. Please wait before retrying.")
            return None
            
        except Exception as e:
            self.logger.error(f"Error in download_single_period: {str(e)}")
            return None
    
    # Alias for compatibility
    download_single_period = descargar_periodo_individual
            
    def download_batch_by_quarters(
        self,
        shapefile_path: str,
        start_year: int,
        end_year: Optional[int] = None,
        output_base_dir: str = "satellite_downloads"
    ) -> List[str]:
        """
        Download data in quarterly batches for multiple years
        
        Args:
            shapefile_path: Path to shapefile
            start_year: Starting year
            end_year: Ending year (current year if None)
            output_base_dir: Base output directory
            
        Returns:
            List of successfully downloaded file paths
        """
        if end_year is None:
            end_year = datetime.now().year
            
        self.logger.info(f"Starting batch download from {start_year} to {end_year}")
        
        downloaded_files = []
        current_date = datetime.now()
        
        for year in range(start_year, end_year + 1):
            self.logger.info(f"Processing year {year}")
            
            # Create year directory
            year_dir = os.path.join(output_base_dir, str(year))
            
            # Define quarters
            quarters = [
                (f"{year}-01-01", f"{year}-03-31", "Q1"),
                (f"{year}-04-01", f"{year}-06-30", "Q2"),
                (f"{year}-07-01", f"{year}-09-30", "Q3"),
                (f"{year}-10-01", f"{year}-12-31", "Q4")
            ]
            
            for start_date, end_date, quarter_name in quarters:
                # Skip future dates
                if year == current_date.year:
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                    if end_dt > current_date:
                        # Adjust end date to current date
                        end_date = current_date.strftime('%Y-%m-%d')
                        
                    # Skip if start date is in the future
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                    if start_dt > current_date:
                        continue
                        
                self.logger.info(f"Downloading {quarter_name} {year}: {start_date} to {end_date}")
                
                try:
                    result_path = self.download_single_period(
                        shapefile_path, start_date, end_date, year_dir
                    )
                    
                    if result_path:
                        downloaded_files.append(result_path)
                        self.logger.info(f"Success: {quarter_name} {year}")
                    else:
                        self.logger.error(f"Failed: {quarter_name} {year}")
                        
                except RateLimitError:
                    self.logger.error(f"Rate limit hit during {quarter_name} {year}. Stopping batch download.")
                    break
                    
                except Exception as e:
                    self.logger.error(f"Error downloading {quarter_name} {year}: {str(e)}")
                    continue
                    
        self.logger.info(f"Batch download completed. Downloaded {len(downloaded_files)} files.")
        return downloaded_files
        
    def run_test_download(self, shapefile_path: str, output_dir: str = "test_download") -> bool:
        """
        Run a test download with recent data
        
        Args:
            shapefile_path: Path to shapefile
            output_dir: Output directory for test
            
        Returns:
            True if test successful, False otherwise
        """
        try:
            self.logger.info("Running test download with recent data...")
            
            # Use last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            result = self.download_single_period(
                shapefile_path,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d'),
                output_dir
            )
            
            if result:
                self.logger.info(f"Test download successful: {result}")
                return True
            else:
                self.logger.error("Test download failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Test download error: {str(e)}")
            return False
            
    def get_download_summary(self, downloaded_files: List[str]) -> dict:
        """Generate summary of downloaded files"""
        summary = {
            'total_files': len(downloaded_files),
            'files_by_year': {},
            'total_size_mb': 0,
            'date_range': {'start': None, 'end': None}
        }
        
        for filepath in downloaded_files:
            try:
                # Extract year from path
                year = Path(filepath).parent.name
                if year.isdigit():
                    summary['files_by_year'][year] = summary['files_by_year'].get(year, 0) + 1
                    
                # Get file size
                size_bytes = Path(filepath).stat().st_size
                summary['total_size_mb'] += size_bytes / (1024 * 1024)
                
                # Extract dates from filename
                filename = Path(filepath).stem
                parts = filename.split('_')
                if len(parts) >= 3:
                    start_date = parts[1]
                    end_date = parts[3]
                    
                    if summary['date_range']['start'] is None or start_date < summary['date_range']['start']:
                        summary['date_range']['start'] = start_date
                    if summary['date_range']['end'] is None or end_date > summary['date_range']['end']:
                        summary['date_range']['end'] = end_date
                        
            except Exception as e:
                self.logger.warning(f"Error processing file {filepath} for summary: {str(e)}")
                
        return summary
    
    # ========================================================================
    # MÉTODOS DE COMPATIBILIDAD PARA INTERFAZ EN INGLÉS
    # ========================================================================
    
    def download_vegetation_index(
        self,
        shapefile_path: str,
        index_name: str,
        start_date: str,
        end_date: str,
        output_dir: str = 'descargas',
        max_cloud_coverage: float = 0.30
    ) -> Optional[str]:
        """
        Descarga un índice de vegetación específico para un período de tiempo.
        Método compatible con interfaz en inglés.
        
        Args:
            shapefile_path: Ruta al shapefile del área de interés
            index_name: Nombre del índice (NDVI, NDRE, MSAVI, RECI, NDMI)
            start_date: Fecha de inicio (YYYY-MM-DD)
            end_date: Fecha de fin (YYYY-MM-DD)
            output_dir: Directorio de salida
            max_cloud_coverage: Cobertura nubosa máxima (0.0-1.0)
            
        Returns:
            Ruta del archivo descargado o None si falla
        """
        # Actualizar configuración de cobertura nubosa si se proporciona
        if max_cloud_coverage != self.config_procesamiento.max_cloud_coverage:
            self.config_procesamiento.max_cloud_coverage = max_cloud_coverage
            self.cliente_api.config_procesamiento.max_cloud_coverage = max_cloud_coverage
        
        # Llamar al método principal en español
        return self.descargar_periodo_individual(
            ruta_shapefile=shapefile_path,
            fecha_inicio=start_date,
            fecha_fin=end_date,
            directorio_salida=output_dir
        )
    
    def download_single_period(
        self,
        shapefile_path: str,
        start_date: str,
        end_date: str,
        output_dir: str = 'descargas'
    ) -> Optional[str]:
        """
        Alias para download_vegetation_index para compatibilidad.
        Descarga un período individual.
        """
        return self.descargar_periodo_individual(
            ruta_shapefile=shapefile_path,
            fecha_inicio=start_date,
            fecha_fin=end_date,
            directorio_salida=output_dir
        )
    
    def download_batch_years(
        self,
        shapefile_path: str,
        start_year: int,
        end_year: int,
        output_dir: str = 'descargas',
        quarters: bool = True
    ) -> List[str]:
        """
        Descarga datos para múltiples años en lotes.
        Método compatible con interfaz en inglés.
        
        Args:
            shapefile_path: Ruta al shapefile
            start_year: Año de inicio
            end_year: Año de fin
            output_dir: Directorio de salida
            quarters: Si True, descarga por trimestres
            
        Returns:
            Lista de rutas de archivos descargados
        """
        if quarters:
            return self.download_batch_by_quarters(
                shapefile_path=shapefile_path,
                start_year=start_year,
                end_year=end_year,
                output_dir=output_dir
            )
        else:
            # Implementación por años completos
            archivos_descargados = []
            for year in range(start_year, end_year + 1):
                start_date = f"{year}-01-01"
                end_date = f"{year}-12-31"
                
                resultado = self.descargar_periodo_individual(
                    ruta_shapefile=shapefile_path,
                    fecha_inicio=start_date,
                    fecha_fin=end_date,
                    directorio_salida=output_dir
                )
                
                if resultado:
                    archivos_descargados.append(resultado)
            
            return archivos_descargados