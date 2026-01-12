#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verificación rápida de dependencias - Tesis_DESCARGAS
Ejecuta esto antes de usar cualquier script del proyecto.
"""

import sys
import warnings

# Suprimir advertencias de versión de Python
warnings.filterwarnings('ignore', category=FutureWarning, module='google.api_core._python_version_support')

def verificar_todo():
    """Verifica las dependencias críticas del proyecto."""
    print("\n🔍 Verificando dependencias críticas...\n")
    
    modulos_criticos = [
        ('rasterio', 'Procesamiento raster'),
        ('fiona', 'Datos vectoriales'),
        ('geopandas', 'Análisis geoespacial'),
        ('ee', 'Google Earth Engine'),
        ('geemap', 'Interfaz Earth Engine'),
        ('numpy', 'Cálculos numéricos'),
        ('pandas', 'Procesamiento datos')
    ]
    
    errores = []
    
    for modulo, desc in modulos_criticos:
        try:
            __import__(modulo)
            print(f"✅ {modulo:12s} - {desc}")
        except ImportError:
            errores.append(modulo)
            print(f"❌ {modulo:12s} - FALTA")
    
    print()
    
    if errores:
        print("❌ ERROR: Instala las dependencias faltantes:")
        print("   pip install --no-cache-dir -r requirements.txt\n")
        return 1
    else:
        print("✅ Sistema listo - Todas las dependencias instaladas\n")
        return 0

if __name__ == '__main__':
    sys.exit(verificar_todo())
