"""
Ejemplo de uso del descargador Sentinel con la API mejorada
"""

import os
import logging
from datetime import datetime, timedelta

from sentinel_downloader import SatelliteDownloader, ConfigurationManager


def setup_environment():
    """Configura las variables de entorno para las credenciales de API"""
    # Necesitas configurar estas variables de entorno antes de ejecutar
    # Opción 1: Configurarlas en el entorno del sistema
    # Opción 2: Configurarlas en un archivo .env
    # Opción 3: Configurarlas directamente aquí (NO recomendado para producción)
    
    # Example (replace with your actual credentials):
    # os.environ['SENTINEL_CLIENT_ID'] = 'your_client_id_here'
    # os.environ['SENTINEL_CLIENT_SECRET'] = 'your_client_secret_here'
    
    # Verificar si las credenciales están configuradas
    if not os.getenv('SENTINEL_CLIENT_ID'):
        print("ERROR: Variable de entorno SENTINEL_CLIENT_ID no configurada")
        print("Por favor configura tus credenciales de Sentinel Hub:")
        print("  set SENTINEL_CLIENT_ID=tu_client_id")
        print("  set SENTINEL_CLIENT_SECRET=tu_client_secret")
        return False
        
    return True


def example_test_download():
    """Ejemplo: Ejecutar una descarga de prueba"""
    print("=== EJEMPLO DE DESCARGA DE PRUEBA ===")
    
    # Tu ruta de shapefile - CAMBIA ESTO por tu shapefile real
    # Ejemplo Windows: r"C:\ruta\a\tu\shapefile.shp"
    # Ejemplo macOS/Linux: "shapefiles/UPIITA_contours_25nov.2025/UPIITA_contours_25Nov2025.shp"
    shapefile_path = "shapefiles/UPIITA_contours_25nov.2025/UPIITA_contours_25Nov2025.shp"
    
    if not os.path.exists(shapefile_path):
        print(f"ERROR: Shapefile no encontrado: {shapefile_path}")
        print("Por favor actualiza la variable shapefile_path con la ruta real de tu archivo")
        return False
        
    try:
        # Inicializar descargador
        downloader = SatelliteDownloader()
        
        # Ejecutar prueba
        success = downloader.run_test_download(shapefile_path, "test_output")
        
        if success:
            print("¡Descarga de prueba completada exitosamente!")
            return True
        else:
            print("La descarga de prueba falló")
            return False
            
    except Exception as e:
        print(f"Error en descarga de prueba: {str(e)}")
        return False


def example_single_download():
    """Ejemplo: Descargar un período de tiempo específico"""
    print("=== EJEMPLO DE DESCARGA DE PERÍODO INDIVIDUAL ===")
    # Ejemplo: "shapefiles/UPIITA_contours_25nov.2025/UPIITA_contours_25Nov2025.shp"
    shapefile_path = "shapefiles/UPIITA_contours_25nov.2025/UPIITA_contours_25Nov2025
    # Tu ruta de shapefile - CAMBIA ESTO
    shapefile_path = r"C:\ruta\a\tu\shapefile.shp"
    
    # Rango de fechas
    start_date = "2023-06-01"
    end_date = "2023-08-31"
    output_dir = "verano_2023"
    
    try:
        downloader = SatelliteDownloader()
        
        result = downloader.download_single_period(
            shapefile_path, start_date, end_date, output_dir
        )
        
        if result:
            print(f"Descarga completada: {result}")
            return True
        else:
            print("La descarga falló")
            return False
            
    except Exception as e:
        print(f"Error en descarga individual: {str(e)}")
        return False


def example_batch_download():
    """Ejemplo: Descargar múltiples años en lotes"""
    # Ejemplo: "shapefiles/UPIITA_contours_25nov.2025/UPIITA_contours_25Nov2025.shp"
    shapefile_path = "shapefiles/UPIITA_contours_25nov.2025/UPIITA_contours_25Nov2025==")
    
    # Tu ruta de shapefile - CAMBIA ESTO
    shapefile_path = r"C:\ruta\a\tu\shapefile.shp"
    
    try:
        downloader = SatelliteDownloader()
        
        # Descargar desde 2022 hasta el año actual
        files = downloader.download_batch_by_quarters(
            shapefile_path, 
            start_year=2022,
            end_year=None,  # Año actual
            output_base_dir="descargas_lotes"
        )
        
        if files:
            summary = downloader.get_download_summary(files)
            print(f"Descarga en lotes completada:")
            print(f"  - Archivos descargados: {summary['total_files']}")
            print(f"  - Tamaño total: {summary['total_size_mb']:.2f} MB")
            print(f"  - Archivos por año: {summary['files_by_year']}")
            return True
        else:
            print("No se descargaron archivos")
            return False
            
    except Exception as e:
        print(f"Error en descarga en lotes: {str(e)}")
        return False


def interactive_mode():
    """Modo interactivo para selección del usuario"""
    print("\n" + "="*60)
    print("DESCARGADOR DE DATOS SATELITALES SENTINEL-2")
    print("="*60)
    
    print("\nOpciones disponibles:")
    print("1. Descarga de prueba (últimos 30 días)")
    print("2. Descarga de período individual")
    print("3. Descarga en lotes (múltiples años)")
    print("0. Salir")
    
    while True:
        try:
            choice = input("\nSelecciona una opción (0-3): ").strip()
            
            if choice == "0":
                print("¡Hasta luego!")
                break
            elif choice == "1":
                if example_test_download():
                    print("\n¡Prueba completada exitosamente!")
                else:
                    print("\nLa prueba falló. Por favor verifica tu configuración.")
            elif choice == "2":
                if example_single_download():
                    print("\n¡Descarga individual completada!")
                else:
                    print("\nLa descarga individual falló.")
            elif choice == "3":
                print("\nADVERTENCIA: La descarga en lotes puede tomar mucho tiempo y usar cuota significativa de API.")
                confirm = input("¿Continuar? (si/no): ").strip().lower()
                if confirm in ['si', 's', 'yes', 'y']:
                    if example_batch_download():
                        print("\n¡Descarga en lotes completada!")
                    else:
                        print("\nLa descarga en lotes falló.")
                else:
                    print("Descarga en lotes cancelada.")
            else:
                print("Opción inválida. Por favor selecciona 0-3.")
                
        except KeyboardInterrupt:
            print("\nSaliendo...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")


def main():
    """Función principal"""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("Configurando entorno...")
    if not setup_environment():
        return
        
    print("¡Entorno listo!")
    
    # Ejecutar modo interactivo
    interactive_mode()


if __name__ == "__main__":
    main()