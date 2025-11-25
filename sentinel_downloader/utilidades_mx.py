# -*- coding: utf-8 -*-
"""
Utilidades adicionales para el sistema de descarga satelital.
Creado con enfoque mexicano para procesamiento eficiente de datos geoespaciales.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging


class UtileriasDescarga:
    """
    Clase de utilidades desarrollada específicamente para el contexto mexicano.
    Incluye funcionalidades para el manejo de datos satelitales en territorio nacional.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Configuración específica para México (zonas horarias, etc.)
        self.zona_horaria_mexico = "America/Mexico_City"
        
    def validar_coordenadas_mexico(self, bbox_coords: tuple) -> bool:
        """
        Valida que las coordenadas estén dentro del territorio mexicano.
        México está aproximadamente entre 14°-33°N y 86°-118°W
        """
        min_lon, min_lat, max_lon, max_lat = bbox_coords
        
        # Límites aproximados de México
        limites_mexico = {
            'lat_min': 14.0,   # Sur (cerca de Chiapas)
            'lat_max': 33.0,   # Norte (cerca de Baja California)
            'lon_min': -118.0, # Oeste (Baja California)
            'lon_max': -86.0   # Este (Península de Yucatán)
        }
        
        # Verificar que las coordenadas estén dentro de México
        coordenadas_validas = (
            limites_mexico['lat_min'] <= min_lat <= limites_mexico['lat_max'] and
            limites_mexico['lat_min'] <= max_lat <= limites_mexico['lat_max'] and
            limites_mexico['lon_min'] <= min_lon <= limites_mexico['lon_max'] and
            limites_mexico['lon_min'] <= max_lon <= limites_mexico['lon_max']
        )
        
        if not coordenadas_validas:
            self.logger.warning("Las coordenadas proporcionadas están fuera del territorio mexicano")
            
        return coordenadas_validas
    
    def generar_reporte_descarga(self, archivos_descargados: List[str], directorio_salida: str) -> str:
        """
        Genera un reporte detallado de la descarga realizada.
        Incluye estadísticas específicas del procesamiento.
        """
        fecha_reporte = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nombre_reporte = f"reporte_descarga_{fecha_reporte}.json"
        ruta_reporte = os.path.join(directorio_salida, nombre_reporte)
        
        # Calcular estadísticas
        estadisticas_descarga = {
            'fecha_generacion': fecha_reporte,
            'total_archivos': len(archivos_descargados),
            'archivos_procesados': [],
            'tamaño_total_mb': 0,
            'periodo_descarga': {'inicio': None, 'fin': None}
        }
        
        # Procesar cada archivo descargado
        for ruta_archivo in archivos_descargados:
            try:
                archivo_info = Path(ruta_archivo)
                if archivo_info.exists():
                    tamaño_archivo = archivo_info.stat().st_size / (1024 * 1024)  # MB
                    estadisticas_descarga['tamaño_total_mb'] += tamaño_archivo
                    
                    info_archivo = {
                        'nombre': archivo_info.name,
                        'ruta_completa': str(archivo_info.absolute()),
                        'tamaño_mb': round(tamaño_archivo, 2),
                        'fecha_creacion': datetime.fromtimestamp(archivo_info.stat().st_ctime).isoformat()
                    }
                    estadisticas_descarga['archivos_procesados'].append(info_archivo)
                    
            except Exception as error:
                self.logger.error(f"Error procesando archivo {ruta_archivo}: {error}")
        
        # Redondear tamaño total
        estadisticas_descarga['tamaño_total_mb'] = round(estadisticas_descarga['tamaño_total_mb'], 2)
        
        # Guardar reporte en formato JSON
        try:
            with open(ruta_reporte, 'w', encoding='utf-8') as archivo_reporte:
                json.dump(estadisticas_descarga, archivo_reporte, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Reporte de descarga generado: {ruta_reporte}")
            return ruta_reporte
            
        except Exception as error:
            self.logger.error(f"Error generando reporte: {error}")
            return ""
    
    def configurar_ambiente_mexicano(self) -> Dict[str, Any]:
        """
        Configura parámetros específicos para el procesamiento de datos en México.
        Incluye configuraciones regionales y temporales.
        """
        configuracion_regional = {
            'formato_fecha': '%d/%m/%Y',  # Formato mexicano DD/MM/YYYY
            'zona_horaria': self.zona_horaria_mexico,
            'idioma_logs': 'es_MX',
            'precision_coordenadas': 6,  # Decimales para coordenadas
            'sistema_medicion': 'metrico',
            'moneda_referencia': 'MXN'
        }
        
        # Configurar variables de entorno si no existen
        variables_entorno = {
            'TZ': self.zona_horaria_mexico,
            'LANG': 'es_MX.UTF-8',
            'LC_ALL': 'es_MX.UTF-8'
        }
        
        for variable, valor in variables_entorno.items():
            if not os.getenv(variable):
                os.environ[variable] = valor
                
        self.logger.info("Configuración regional mexicana aplicada")
        return configuracion_regional
    
    def calcular_tiempo_estimado_descarga(self, num_archivos: int, tamaño_promedio_mb: float = 50) -> str:
        """
        Calcula tiempo estimado de descarga basado en estadísticas empíricas.
        Considera la velocidad de internet promedio en México.
        """
        # Velocidad promedio de internet en México (aproximada)
        velocidad_promedio_mbps = 25  # Mbps
        velocidad_mb_por_segundo = velocidad_promedio_mbps / 8  # MB/s
        
        # Tiempo estimado por archivo (incluyendo procesamiento)
        tiempo_por_archivo_segundos = (tamaño_promedio_mb / velocidad_mb_por_segundo) + 10  # +10s procesamiento
        tiempo_total_segundos = num_archivos * tiempo_por_archivo_segundos
        
        # Convertir a formato legible
        if tiempo_total_segundos < 60:
            return f"{int(tiempo_total_segundos)} segundos"
        elif tiempo_total_segundos < 3600:
            minutos = int(tiempo_total_segundos / 60)
            return f"{minutos} minutos"
        else:
            horas = int(tiempo_total_segundos / 3600)
            minutos = int((tiempo_total_segundos % 3600) / 60)
            return f"{horas} horas y {minutos} minutos"


def inicializar_sistema_mexicano():
    """
    Función de inicialización específica para el contexto mexicano.
    Se ejecuta automáticamente al importar el módulo.
    """
    utilidades = UtileriasDescarga()
    configuracion = utilidades.configurar_ambiente_mexicano()
    
    # Mostrar mensaje de bienvenida en español
    print("="*60)
    print("SISTEMA DE DESCARGA SATELITAL PARA MÉXICO")
    print("Desarrollado para el procesamiento eficiente de datos Sentinel-2")
    print("="*60)
    
    return configuracion


# Auto-inicialización del sistema
_CONFIG_REGIONAL = inicializar_sistema_mexicano()