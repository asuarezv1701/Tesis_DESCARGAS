#!/usr/bin/env python3
"""
Descargador de Imágenes Satelitales por Índice de Vegetación
Permite seleccionar índices específicos y organizar descargas por tipo
"""

import os
import glob
from pathlib import Path
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class GestorIndicesVegetacion:
    """Gestor para organizar descargas por índice de vegetación"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.shapefiles_dir = self.base_dir / "shapefiles"
        self.descargas_dir = self.base_dir / "descargas"
        
        # Definir índices disponibles con sus descripciones
        self.indices_disponibles = {
            'NDVI': {
                'nombre': 'Normalized Difference Vegetation Index',
                'descripcion': 'Índice general de salud vegetal',
                'uso': 'Monitoreo de cultivos y vegetación general'
            },
            'NDRE': {
                'nombre': 'Normalized Difference Red Edge',
                'descripcion': 'Sensible al contenido de clorofila',
                'uso': 'Cultivos densos y análisis de clorofila'
            },
            'MSAVI': {
                'nombre': 'Modified Soil Adjusted Vegetation Index',
                'descripcion': 'Minimiza influencia del suelo',
                'uso': 'Vegetación dispersa y cultivos tempranos'
            },
            'RECI': {
                'nombre': 'Red Edge Chlorophyll Index',
                'descripcion': 'Específico para contenido de clorofila',
                'uso': 'Evaluación nutricional y biomasa'
            },
            'NDMI': {
                'nombre': 'Normalized Difference Moisture Index',
                'descripcion': 'Mide contenido de humedad',
                'uso': 'Estrés hídrico y planificación de riego'
            }
        }
    
    def mostrar_menu_indices(self):
        """Muestra el menú de selección de índices"""
        print("\n" + "="*70)
        print("🌱 SELECCIÓN DE ÍNDICE DE VEGETACIÓN 🌱")
        print("="*70)
        
        for i, (codigo, info) in enumerate(self.indices_disponibles.items(), 1):
            print(f"\n{i}. {codigo} - {info['nombre']}")
            print(f"   📊 {info['descripcion']}")
            print(f"   🎯 Uso: {info['uso']}")
        
        print(f"\n{len(self.indices_disponibles) + 1}. TODOS - Descargar todos los índices")
        print("0. Salir")
        return self.seleccionar_indice()
    
    def seleccionar_indice(self):
        """Permite al usuario seleccionar un índice"""
        while True:
            try:
                seleccion = input(f"\nSelecciona una opción (0-{len(self.indices_disponibles) + 1}): ").strip()
                
                if seleccion == "0":
                    return None
                elif seleccion == str(len(self.indices_disponibles) + 1):
                    return list(self.indices_disponibles.keys())
                elif 1 <= int(seleccion) <= len(self.indices_disponibles):
                    codigo_indice = list(self.indices_disponibles.keys())[int(seleccion) - 1]
                    return [codigo_indice]
                else:
                    print("❌ Opción inválida. Intenta de nuevo.")
                    
            except ValueError:
                print("❌ Por favor ingresa un número válido.")
    
    def buscar_shapefiles(self, indice):
        """Busca shapefiles en la carpeta del índice especificado"""
        carpeta_indice = self.shapefiles_dir / indice
        
        if not carpeta_indice.exists():
            return []
            
        # Buscar archivos .shp
        shapefiles = list(carpeta_indice.glob("*.shp"))
        return shapefiles
    
    def mostrar_shapefiles_disponibles(self, indice):
        """Muestra los shapefiles disponibles para un índice"""
        shapefiles = self.buscar_shapefiles(indice)
        
        if not shapefiles:
            print(f"\n⚠️  No se encontraron shapefiles en la carpeta {indice}")
            print(f"📁 Coloca tus archivos .shp en: {self.shapefiles_dir / indice}")
            return None
            
        print(f"\n📁 Shapefiles disponibles para {indice}:")
        print("-" * 50)
        
        for i, shapefile in enumerate(shapefiles, 1):
            print(f"{i}. {shapefile.name}")
            
        return shapefiles
    
    def seleccionar_shapefile(self, shapefiles):
        """Permite seleccionar un shapefile de la lista"""
        while True:
            try:
                seleccion = input(f"\nSelecciona un shapefile (1-{len(shapefiles)}): ").strip()
                indice_sel = int(seleccion) - 1
                
                if 0 <= indice_sel < len(shapefiles):
                    return shapefiles[indice_sel]
                else:
                    print("❌ Opción inválida. Intenta de nuevo.")
                    
            except ValueError:
                print("❌ Por favor ingresa un número válido.")
    
    def ejecutar_descarga(self, indices_seleccionados):
        """Ejecuta la descarga para los índices seleccionados"""
        from sentinel_downloader import SatelliteDownloader
        
        try:
            downloader = SatelliteDownloader()
            resultados = {}
            
            for indice in indices_seleccionados:
                print(f"\n🔍 Procesando índice: {indice}")
                print("=" * 50)
                
                # Mostrar shapefiles disponibles
                shapefiles = self.mostrar_shapefiles_disponibles(indice)
                if not shapefiles:
                    print(f"⏭️  Saltando {indice} - sin shapefiles")
                    continue
                
                # Seleccionar shapefile
                shapefile_seleccionado = self.seleccionar_shapefile(shapefiles)
                
                # Configurar directorio de salida
                output_dir = self.descargas_dir / indice / datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir.mkdir(parents=True, exist_ok=True)
                
                print(f"\n🚀 Iniciando descarga para {indice}...")
                print(f"📁 Shapefile: {shapefile_seleccionado.name}")
                print(f"📁 Salida: {output_dir}")
                
                # Ejecutar descarga de prueba
                exito = downloader.run_test_download(
                    str(shapefile_seleccionado), 
                    str(output_dir)
                )
                
                resultados[indice] = {
                    'exito': exito,
                    'shapefile': shapefile_seleccionado.name,
                    'output': output_dir
                }
                
                if exito:
                    print(f"✅ {indice}: Descarga completada exitosamente")
                else:
                    print(f"❌ {indice}: Error en la descarga")
            
            return resultados
            
        except Exception as e:
            print(f"❌ Error durante la descarga: {str(e)}")
            return {}
    
    def mostrar_resumen(self, resultados):
        """Muestra un resumen de las descargas realizadas"""
        print("\n" + "="*70)
        print("📊 RESUMEN DE DESCARGAS")
        print("="*70)
        
        exitosas = 0
        fallidas = 0
        
        for indice, resultado in resultados.items():
            estado = "✅ EXITOSA" if resultado['exito'] else "❌ FALLIDA"
            print(f"\n{indice}: {estado}")
            print(f"   📁 Shapefile: {resultado['shapefile']}")
            print(f"   📁 Salida: {resultado['output']}")
            
            if resultado['exito']:
                exitosas += 1
            else:
                fallidas += 1
        
        print(f"\n📊 Total: {exitosas} exitosas, {fallidas} fallidas")


def main():
    """Función principal del gestor de índices"""
    print("🌍 DESCARGADOR DE IMÁGENES SATELITALES POR ÍNDICE")
    print("=" * 60)
    
    # Verificar credenciales
    if not os.getenv('SENTINEL_CLIENT_ID') or not os.getenv('SENTINEL_CLIENT_SECRET'):
        print("❌ Error: Credenciales no configuradas")
        print("Por favor configura tu archivo .env con las credenciales de Sentinel Hub")
        return
    
    gestor = GestorIndicesVegetacion()
    
    # Mostrar menú y seleccionar índices
    indices_seleccionados = gestor.mostrar_menu_indices()
    
    if not indices_seleccionados:
        print("👋 ¡Hasta luego!")
        return
    
    print(f"\n🎯 Índices seleccionados: {', '.join(indices_seleccionados)}")
    
    # Ejecutar descargas
    resultados = gestor.ejecutar_descarga(indices_seleccionados)
    
    # Mostrar resumen
    if resultados:
        gestor.mostrar_resumen(resultados)
    
    input("\nPresiona Enter para salir...")


if __name__ == "__main__":
    main()