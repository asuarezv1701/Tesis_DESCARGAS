"""
Script de Verificación Completa del Sistema
===========================================

Verifica que todos los componentes del descargador interactivo
estén correctamente instalados y configurados.

Fecha: 13 de noviembre de 2025
Versión: 1.0
"""

import sys
import os
from pathlib import Path
from datetime import datetime


# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    """Imprime un encabezado"""
    print(f"\n{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.CYAN}{'='*80}{Colors.END}\n")


def print_success(text):
    """Imprime mensaje de éxito"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text):
    """Imprime mensaje de error"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text):
    """Imprime mensaje de advertencia"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text):
    """Imprime mensaje informativo"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")


def verificar_python():
    """Verifica la versión de Python"""
    print_header("VERIFICACIÓN DE PYTHON")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    print_info(f"Versión de Python: {version_str}")
    
    if version.major == 3 and version.minor >= 8:
        print_success("Versión de Python compatible")
        return True
    else:
        print_error(f"Se requiere Python 3.8 o superior (actual: {version_str})")
        return False


def verificar_paquetes():
    """Verifica que los paquetes necesarios estén instalados"""
    print_header("VERIFICACIÓN DE PAQUETES")
    
    paquetes_requeridos = {
        'sentinelhub': '3.11.3',
        'geopandas': '1.1.1',
        'rasterio': '1.4.3',
        'numpy': '2.2.6',
        'matplotlib': '3.9.2',
        'pandas': '2.2.3',
        'shapely': None,
        'fiona': None,
        'pyproj': None,
    }
    
    todos_ok = True
    
    for paquete, version_esperada in paquetes_requeridos.items():
        try:
            modulo = __import__(paquete)
            version_instalada = getattr(modulo, '__version__', 'desconocida')
            
            if version_esperada:
                if version_instalada == version_esperada:
                    print_success(f"{paquete}: {version_instalada} ✓")
                else:
                    print_warning(f"{paquete}: {version_instalada} (esperada: {version_esperada})")
            else:
                print_success(f"{paquete}: {version_instalada} ✓")
                
        except ImportError:
            print_error(f"{paquete}: NO INSTALADO")
            todos_ok = False
    
    return todos_ok


def verificar_estructura_archivos():
    """Verifica que los archivos del proyecto existan"""
    print_header("VERIFICACIÓN DE ESTRUCTURA DE ARCHIVOS")
    
    archivos_requeridos = [
        'descargador_interactivo.py',
        'GUIA_DESCARGADOR_INTERACTIVO.md',
        'PRUEBA_DESCARGADOR_INTERACTIVO.md',
        'configurar_credenciales.ps1',
        'requirements.txt',
        'README.md',
        'sentinel_downloader/__init__.py',
        'sentinel_downloader/config.py',
        'sentinel_downloader/downloader.py',
        'sentinel_downloader/indices.py',
        'sentinel_downloader/geometry.py',
        'sentinel_downloader/api_client.py',
        'sentinel_downloader/file_manager.py',
    ]
    
    todos_ok = True
    
    for archivo in archivos_requeridos:
        ruta = Path(archivo)
        if ruta.exists():
            tamaño = ruta.stat().st_size
            print_success(f"{archivo} ({tamaño:,} bytes)")
        else:
            print_error(f"{archivo} - NO ENCONTRADO")
            todos_ok = False
    
    return todos_ok


def verificar_directorios():
    """Verifica que los directorios necesarios existan"""
    print_header("VERIFICACIÓN DE DIRECTORIOS")
    
    directorios = {
        'descargas': 'Directorio para archivos descargados',
        'logs': 'Directorio para logs del sistema',
        'shapefiles': 'Directorio con shapefiles de áreas',
        'sentinel_downloader': 'Módulo principal del sistema',
    }
    
    todos_ok = True
    
    for directorio, descripcion in directorios.items():
        ruta = Path(directorio)
        if ruta.exists() and ruta.is_dir():
            archivos = len(list(ruta.iterdir()))
            print_success(f"{directorio}/ - {descripcion} ({archivos} elementos)")
        else:
            print_warning(f"{directorio}/ - NO EXISTE (se creará automáticamente)")
    
    return todos_ok


def verificar_imports():
    """Verifica que los módulos del proyecto se puedan importar"""
    print_header("VERIFICACIÓN DE IMPORTS")
    
    imports_requeridos = [
        ('sentinel_downloader', 'SatelliteDownloader'),
        ('sentinel_downloader', 'ConfigurationManager'),
        ('sentinel_downloader.indices', 'VegetationIndicesProcessor'),
        ('sentinel_downloader.geometry', 'GeometryHandler'),
        ('sentinel_downloader.api_client', 'SentinelHubClient'),
        ('sentinel_downloader.downloader', 'ImageDownloader'),
    ]
    
    todos_ok = True
    
    for modulo_nombre, clase_nombre in imports_requeridos:
        try:
            modulo = __import__(modulo_nombre, fromlist=[clase_nombre])
            clase = getattr(modulo, clase_nombre)
            print_success(f"{modulo_nombre}.{clase_nombre}")
        except ImportError as e:
            print_error(f"{modulo_nombre}.{clase_nombre} - ERROR: {e}")
            todos_ok = False
        except AttributeError as e:
            print_error(f"{modulo_nombre}.{clase_nombre} - NO ENCONTRADO: {e}")
            todos_ok = False
    
    return todos_ok


def verificar_credenciales():
    """Verifica si las credenciales están configuradas"""
    print_header("VERIFICACIÓN DE CREDENCIALES")
    
    client_id = os.getenv('SENTINEL_CLIENT_ID')
    client_secret = os.getenv('SENTINEL_CLIENT_SECRET')
    
    if client_id and client_secret:
        print_success("SENTINEL_CLIENT_ID configurado")
        print_success("SENTINEL_CLIENT_SECRET configurado")
        print_info(f"Client ID: {client_id[:8]}...{client_id[-4:]}")
        return True
    else:
        print_warning("Credenciales NO configuradas")
        import sys
        if sys.platform == 'win32':
            print_info("Ejecuta: .\\configurar_credenciales.ps1")
            print_info("O configura manualmente:")
            print_info("  $env:SENTINEL_CLIENT_ID = 'tu_client_id'")
            print_info("  $env:SENTINEL_CLIENT_SECRET = 'tu_client_secret'")
        else:
            print_info("Configura las credenciales en tu shell:")
            print_info("  export SENTINEL_CLIENT_ID='tu_client_id'")
            print_info("  export SENTINEL_CLIENT_SECRET='tu_client_secret'")
            print_info("O crea un archivo .env en la raíz del proyecto")
        return False


def verificar_shapefiles():
    """Verifica shapefiles disponibles"""
    print_header("VERIFICACIÓN DE SHAPEFILES")
    
    shapefiles = list(Path('.').glob('**/*.shp'))
    
    if shapefiles:
        print_success(f"Encontrados {len(shapefiles)} shapefiles:")
        for shp in shapefiles[:10]:  # Mostrar máximo 10
            tamaño = shp.stat().st_size
            print_info(f"  {shp} ({tamaño:,} bytes)")
        
        if len(shapefiles) > 10:
            print_info(f"  ... y {len(shapefiles) - 10} más")
        
        return True
    else:
        print_warning("No se encontraron shapefiles")
        print_info("Agrega al menos un shapefile (.shp) para pruebas")
        return False


def verificar_funcionalidad_basica():
    """Verifica funcionalidad básica del sistema"""
    print_header("VERIFICACIÓN DE FUNCIONALIDAD BÁSICA")
    
    try:
        # Intentar importar y crear instancia del descargador
        from sentinel_downloader import SatelliteDownloader
        print_success("SatelliteDownloader importado correctamente")
        
        # Verificar que la clase tenga los métodos esperados
        metodos_requeridos = [
            'download_vegetation_index',
            'download_single_period',
            'download_batch_years',
        ]
        
        for metodo in metodos_requeridos:
            if hasattr(SatelliteDownloader, metodo):
                print_success(f"Método '{metodo}' disponible")
            else:
                print_error(f"Método '{metodo}' NO encontrado")
                return False
        
        return True
        
    except Exception as e:
        print_error(f"Error al verificar funcionalidad: {e}")
        return False


def generar_reporte_final(resultados):
    """Genera un reporte final de la verificación"""
    print_header("REPORTE FINAL")
    
    total = len(resultados)
    exitosos = sum(resultados.values())
    
    print(f"{Colors.BOLD}Total de verificaciones:{Colors.END} {total}")
    print(f"{Colors.GREEN}Exitosas:{Colors.END} {exitosos}")
    print(f"{Colors.RED}Fallidas:{Colors.END} {total - exitosos}")
    
    print(f"\n{Colors.BOLD}Detalle por componente:{Colors.END}\n")
    
    for nombre, resultado in resultados.items():
        estado = f"{Colors.GREEN}✅ OK{Colors.END}" if resultado else f"{Colors.RED}❌ FALLO{Colors.END}"
        print(f"  {nombre}: {estado}")
    
    print(f"\n{Colors.CYAN}{'='*80}{Colors.END}")
    
    if exitosos == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ SISTEMA COMPLETAMENTE FUNCIONAL{Colors.END}")
        print(f"\n{Colors.CYAN}¡Listo para ejecutar:{Colors.END}")
        print(f"{Colors.BOLD}  python descargador_interactivo.py{Colors.END}\n")
        return True
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  SISTEMA PARCIALMENTE FUNCIONAL{Colors.END}")
        print(f"\n{Colors.CYAN}Revisa los componentes marcados como FALLO{Colors.END}\n")
        return False


def main():
    """Función principal"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}╔═══════════════════════════════════════════════════════════════════════════════╗{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}║                                                                               ║{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}║         VERIFICACIÓN COMPLETA DEL SISTEMA DE DESCARGA SENTINEL-2              ║{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}║                                                                               ║{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.END}")
    
    print(f"\n{Colors.CYAN}Fecha: {datetime.now().strftime('%d de %B de %Y, %H:%M:%S')}{Colors.END}")
    print(f"{Colors.CYAN}Directorio: {Path.cwd()}{Colors.END}")
    
    # Ejecutar todas las verificaciones
    resultados = {
        'Python': verificar_python(),
        'Paquetes': verificar_paquetes(),
        'Archivos': verificar_estructura_archivos(),
        'Directorios': verificar_directorios(),
        'Imports': verificar_imports(),
        'Credenciales': verificar_credenciales(),
        'Shapefiles': verificar_shapefiles(),
        'Funcionalidad': verificar_funcionalidad_basica(),
    }
    
    # Generar reporte final
    sistema_ok = generar_reporte_final(resultados)
    
    # Retornar código de salida
    sys.exit(0 if sistema_ok else 1)


if __name__ == "__main__":
    main()
