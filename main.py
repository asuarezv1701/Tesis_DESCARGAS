"""
Interfaz de línea de comandos para el descargador Sentinel
"""

import sys
import argparse
import logging
from pathlib import Path

from sentinel_downloader import SatelliteDownloader, ConfigurationManager


def configurar_logging_cli(detallado: bool = False):
    """Configura el sistema de logging para uso desde línea de comandos"""
    nivel_logging = logging.DEBUG if detallado else logging.INFO
    
    logging.basicConfig(
        level=nivel_logging,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def main():
    """Punto de entrada principal de la interfaz de línea de comandos"""
    analizador_args = argparse.ArgumentParser(
        description='Descarga imágenes satelitales Sentinel-2 e índices de vegetación',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Descarga de prueba con datos recientes
  python main.py test --shapefile /ruta/a/area.shp
  
  # Descarga de período individual
  python main.py single --shapefile /ruta/a/area.shp --start 2023-01-01 --end 2023-03-31
  
  # Descarga en lotes por años
  python main.py batch --shapefile /ruta/a/area.shp --start-year 2020 --end-year 2023
        """
    )
    
    analizador_args.add_argument('--verbose', '-v', action='store_true', help='Habilitar logging detallado')
    
    subparsers = analizador_args.add_subparsers(dest='comando', help='Comandos disponibles')
    
    # Comando de prueba
    parser_prueba = subparsers.add_parser('test', help='Ejecutar descarga de prueba')
    parser_prueba.add_argument('--shapefile', required=True, help='Ruta al shapefile')
    parser_prueba.add_argument('--output', default='salida_prueba', help='Directorio de salida')
    
    # Comando de descarga individual
    parser_individual = subparsers.add_parser('single', help='Descargar período de tiempo individual')
    parser_individual.add_argument('--shapefile', required=True, help='Ruta al shapefile')
    parser_individual.add_argument('--start', required=True, help='Fecha de inicio (YYYY-MM-DD)')
    parser_individual.add_argument('--end', required=True, help='Fecha de fin (YYYY-MM-DD)')
    parser_individual.add_argument('--output', required=True, help='Directorio de salida')
    
    # Comando de descarga en lotes
    parser_lotes = subparsers.add_parser('batch', help='Descargar múltiples períodos')
    parser_lotes.add_argument('--shapefile', required=True, help='Ruta al shapefile')
    parser_lotes.add_argument('--start-year', type=int, required=True, help='Año de inicio')
    parser_lotes.add_argument('--end-year', type=int, help='Año de fin (año actual si no se especifica)')
    parser_lotes.add_argument('--output', default='descargas_lotes', help='Directorio base de salida')
    
    argumentos = analizador_args.parse_args()
    
    if not argumentos.comando:
        analizador_args.print_help()
        sys.exit(1)
        
    # Configurar sistema de logging
    configurar_logging_cli(argumentos.verbose)
    registro_logger = logging.getLogger(__name__)
    
    try:
        # Inicializar descargador satelital
        gestor_configuracion = ConfigurationManager()
        descargador = DescargadorSatelital(gestor_configuracion)
        
        # Probar configuración del sistema
        configuracion_exitosa = descargador.probar_configuracion()
        if not configuracion_exitosa:
            registro_logger.error("Falló la prueba de configuración. Por favor verifica tu configuración.")
            sys.exit(1)
            
        # Execute commands
        if args.command == 'test':
            logger.info("Running test download...")
            success = downloader.run_test_download(args.shapefile, args.output)
            if success:
                logger.info("Test completed successfully")
                sys.exit(0)
            else:
                logger.error("Test failed")
                sys.exit(1)
                
        elif args.command == 'single':
            logger.info(f"Downloading period {args.start} to {args.end}")
            result = downloader.download_single_period(
                args.shapefile, args.start, args.end, args.output
            )
            if result:
                logger.info(f"Download completed: {result}")
                sys.exit(0)
            else:
                logger.error("Download failed")
                sys.exit(1)
                
        elif args.command == 'batch':
            logger.info(f"Starting batch download from {args.start_year}")
            files = downloader.download_batch_by_quarters(
                args.shapefile, args.start_year, args.end_year, args.output
            )
            
            if files:
                summary = downloader.get_download_summary(files)
                logger.info(f"Batch download completed:")
                logger.info(f"  - Total files: {summary['total_files']}")
                logger.info(f"  - Total size: {summary['total_size_mb']:.2f} MB")
                logger.info(f"  - Date range: {summary['date_range']['start']} to {summary['date_range']['end']}")
                sys.exit(0)
            else:
                logger.error("Batch download failed")
                sys.exit(1)
                
    except KeyboardInterrupt:
        logger.info("Download interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()