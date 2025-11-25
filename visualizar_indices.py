#!/usr/bin/env python3
"""
Script para visualizar índices de vegetación con paletas de colores específicas
Genera mapas clasificados para NDVI, NDRE, MSAVI, RECI y NDMI

Autor: Sistema de Descarga Sentinel-2
Fecha: 13 de noviembre de 2025
"""

import os
import sys
from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Rectangle
import pandas as pd
from datetime import datetime

# Configuración de paletas de colores por índice
PALETAS_COLORES = {
    'NDVI': {
        'colors': ['#8B0000', '#FF4500', '#FFA500', '#FFD700', '#ADFF2F', 
                   '#7FFF00', '#00FF00', '#008000', '#006400'],
        'bounds': [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0],
        'labels': ['0.0-0.1', '0.1-0.2', '0.2-0.3', '0.3-0.4', '0.4-0.5', 
                   '0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-1.0'],
        'titulo': 'Índice de Vegetación NDVI',
        'descripcion': 'Verde oscuro = Vegetación densa | Amarillo-Rojo = Suelo/Estrés'
    },
    'NDRE': {
        'colors': ['#D2B48C', '#F0E68C', '#FFFF66', '#CCFF33', '#66FF00', '#00CC00'],
        'bounds': [0.0, 0.15, 0.3, 0.45, 0.6, 0.75, 1.0],
        'labels': ['0.0-0.15', '0.15-0.3', '0.3-0.45', '0.45-0.6', '0.6-0.75', '0.75+'],
        'titulo': 'Índice Red Edge (NDRE)',
        'descripcion': 'Verde = Alta clorofila | Amarillo-Beige = Baja clorofila'
    },
    'MSAVI': {
        'colors': ['#654321', '#CD5C5C', '#FF6347', '#FFA500', '#FFD700', 
                   '#ADFF2F', '#7FFF00', '#32CD32'],
        'bounds': [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0],
        'labels': ['0.0-0.1', '0.1-0.2', '0.2-0.3', '0.3-0.4', '0.4-0.5', 
                   '0.5-0.6', '0.6-0.7', '0.7+'],
        'titulo': 'Índice MSAVI (Ajustado por Suelo)',
        'descripcion': 'Verde = Buena cobertura | Marrón-Naranja = Suelo expuesto'
    },
    'RECI': {
        'colors': ['#FFFACD', '#FFE4B5', '#FFDAB9', '#FFA500', '#FF8C00', 
                   '#FF6347', '#FF4500', '#DC143C', '#B22222', '#8B0000'],
        'bounds': [0.5, 0.7, 0.9, 1.1, 1.3, 1.5, 1.7, 2.0, 2.5, 3.0, 5.0],
        'labels': ['0.5-0.7', '0.7-0.9', '0.9-1.1', '1.1-1.3', '1.3-1.5', 
                   '1.5-1.7', '1.7-2.0', '2.0-2.5', '2.5-3.0', '3.0+'],
        'titulo': 'Índice de Clorofila RECI',
        'descripcion': 'Rojo oscuro = Alta clorofila | Amarillo = Baja clorofila'
    },
    'NDMI': {
        'colors': ['#8B4513', '#CD853F', '#DEB887', '#B0E0E6', '#87CEEB', 
                   '#4682B4', '#1E90FF', '#0000FF', '#00008B'],
        'bounds': [-0.2, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0],
        'labels': ['-0.2-0.0', '0.0-0.1', '0.1-0.2', '0.2-0.3', '0.3-0.4', 
                   '0.4-0.5', '0.5-0.6', '0.6-0.7', '0.7+'],
        'titulo': 'Índice de Humedad NDMI',
        'descripcion': 'Azul oscuro = Alta humedad | Marrón = Estrés hídrico'
    }
}


def encontrar_archivo_mas_reciente(indice):
    """
    Encuentra el shapefile más reciente para un índice específico
    
    Args:
        indice: Nombre del índice (NDVI, NDRE, MSAVI, RECI, NDMI)
    
    Returns:
        Path del shapefile o None si no se encuentra
    """
    ruta_descargas = Path('./descargas') / indice
    
    if not ruta_descargas.exists():
        print(f"⚠️ No se encontró la carpeta: {ruta_descargas}")
        return None
    
    # Buscar todos los shapefiles de píxeles válidos
    shapefiles = list(ruta_descargas.rglob('*_pixeles_validos.shp'))
    
    if not shapefiles:
        print(f"⚠️ No se encontraron shapefiles en: {ruta_descargas}")
        return None
    
    # Obtener el más reciente por fecha de modificación
    shapefile_reciente = max(shapefiles, key=lambda p: p.stat().st_mtime)
    return shapefile_reciente


def visualizar_indice(indice, shapefile_path=None, guardar=True):
    """
    Visualiza un índice de vegetación con su paleta de colores específica
    
    Args:
        indice: Nombre del índice (NDVI, NDRE, MSAVI, RECI, NDMI)
        shapefile_path: Ruta al shapefile (opcional, busca automáticamente)
        guardar: Si True, guarda la imagen
    """
    print(f"\n{'='*60}")
    print(f"Visualizando índice: {indice}")
    print(f"{'='*60}")
    
    # Buscar shapefile si no se proporciona
    if shapefile_path is None:
        shapefile_path = encontrar_archivo_mas_reciente(indice)
        if shapefile_path is None:
            return False
    
    print(f"📂 Archivo: {shapefile_path}")
    
    # Cargar datos
    try:
        gdf = gpd.read_file(shapefile_path)
        print(f"✅ Datos cargados: {len(gdf)} píxeles")
    except Exception as e:
        print(f"❌ Error al cargar shapefile: {e}")
        return False
    
    # Verificar que el índice existe en los datos
    if indice not in gdf.columns:
        print(f"❌ El índice '{indice}' no se encuentra en los datos")
        print(f"   Columnas disponibles: {gdf.columns.tolist()}")
        return False
    
    # Filtrar valores válidos
    gdf_validos = gdf[gdf[indice].notna()].copy()
    print(f"📊 Píxeles válidos: {len(gdf_validos)}")
    
    if len(gdf_validos) == 0:
        print(f"⚠️ No hay datos válidos para {indice}")
        return False
    
    # Estadísticas
    print(f"\n📈 Estadísticas de {indice}:")
    print(f"   Mínimo:  {gdf_validos[indice].min():.4f}")
    print(f"   Máximo:  {gdf_validos[indice].max():.4f}")
    print(f"   Media:   {gdf_validos[indice].mean():.4f}")
    print(f"   Mediana: {gdf_validos[indice].median():.4f}")
    
    # Obtener configuración de paleta
    config = PALETAS_COLORES[indice]
    cmap = mcolors.ListedColormap(config['colors'])
    norm = mcolors.BoundaryNorm(config['bounds'], cmap.N)
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(14, 12))
    
    # Plotear datos
    gdf_validos.plot(
        column=indice,
        ax=ax,
        cmap=cmap,
        norm=norm,
        edgecolor='none',
        legend=False,
        markersize=20,
        alpha=0.9
    )
    
    # Configurar título y etiquetas
    ax.set_title(config['titulo'], fontsize=18, fontweight='bold', pad=20)
    ax.set_xlabel('Longitud', fontsize=12)
    ax.set_ylabel('Latitud', fontsize=12)
    
    # Agregar descripción
    ax.text(0.5, -0.08, config['descripcion'], 
            transform=ax.transAxes,
            ha='center', fontsize=10, style='italic',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    # Crear leyenda personalizada
    legend_elements = []
    for i, (color, label) in enumerate(zip(config['colors'], config['labels'])):
        legend_elements.append(
            Rectangle((0, 0), 1, 1, fc=color, edgecolor='black', linewidth=0.5, label=label)
        )
    
    # Agregar leyenda
    legend = ax.legend(
        handles=legend_elements,
        title=f'Rangos de {indice}',
        loc='center left',
        bbox_to_anchor=(1, 0.5),
        fontsize=10,
        title_fontsize=12,
        frameon=True,
        fancybox=True,
        shadow=True
    )
    
    # Agregar información adicional
    info_text = f"Píxeles: {len(gdf_validos)}\n"
    info_text += f"Rango: {gdf_validos[indice].min():.3f} - {gdf_validos[indice].max():.3f}\n"
    info_text += f"Media: {gdf_validos[indice].mean():.3f}"
    
    ax.text(0.02, 0.98, info_text,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Agregar fecha
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    ax.text(0.98, 0.02, f'Generado: {fecha_actual}',
            transform=ax.transAxes,
            fontsize=8,
            ha='right',
            va='bottom',
            style='italic',
            color='gray')
    
    plt.tight_layout()
    
    # Guardar imagen
    if guardar:
        output_dir = Path('./visualizaciones')
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f'mapa_{indice}_{timestamp}.png'
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"\n💾 Imagen guardada: {output_file}")
    
    plt.show()
    return True


def visualizar_todos_indices():
    """
    Visualiza todos los índices disponibles
    """
    print("\n" + "="*60)
    print("VISUALIZACIÓN DE TODOS LOS ÍNDICES DE VEGETACIÓN")
    print("="*60)
    
    indices = ['NDVI', 'NDRE', 'MSAVI', 'RECI', 'NDMI']
    resultados = []
    
    for indice in indices:
        exito = visualizar_indice(indice)
        resultados.append((indice, exito))
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE VISUALIZACIÓN")
    print("="*60)
    
    for indice, exito in resultados:
        estado = "✅ Exitoso" if exito else "❌ Fallido"
        print(f"{indice:10s} : {estado}")
    
    exitosos = sum(1 for _, e in resultados if e)
    print(f"\nTotal: {exitosos}/{len(indices)} índices visualizados correctamente")


def generar_informe_estadistico(indice):
    """
    Genera un informe estadístico detallado para un índice
    
    Args:
        indice: Nombre del índice (NDVI, NDRE, MSAVI, RECI, NDMI)
    """
    shapefile_path = encontrar_archivo_mas_reciente(indice)
    if shapefile_path is None:
        return
    
    # Cargar datos
    gdf = gpd.read_file(shapefile_path)
    gdf_validos = gdf[gdf[indice].notna()].copy()
    
    # Aplicar clasificación según rangos
    config = PALETAS_COLORES[indice]
    gdf_validos['Clase'] = pd.cut(
        gdf_validos[indice],
        bins=config['bounds'],
        labels=config['labels'],
        include_lowest=True
    )
    
    # Generar estadísticas por clase
    print(f"\n{'='*60}")
    print(f"INFORME ESTADÍSTICO: {indice}")
    print(f"{'='*60}\n")
    
    print("Distribución por clases:")
    print("-" * 60)
    
    distribucion = gdf_validos['Clase'].value_counts().sort_index()
    total_pixeles = len(gdf_validos)
    
    for clase, cantidad in distribucion.items():
        porcentaje = (cantidad / total_pixeles) * 100
        barra = '█' * int(porcentaje / 2)
        print(f"{clase:15s} | {cantidad:5d} píxeles ({porcentaje:5.1f}%) {barra}")
    
    # Estadísticas generales
    print(f"\n{'='*60}")
    print("Estadísticas Generales:")
    print("-" * 60)
    print(f"Total píxeles válidos:  {total_pixeles}")
    print(f"Mínimo:                 {gdf_validos[indice].min():.4f}")
    print(f"Máximo:                 {gdf_validos[indice].max():.4f}")
    print(f"Media:                  {gdf_validos[indice].mean():.4f}")
    print(f"Mediana:                {gdf_validos[indice].median():.4f}")
    print(f"Desviación estándar:    {gdf_validos[indice].std():.4f}")
    print(f"Percentil 25:           {gdf_validos[indice].quantile(0.25):.4f}")
    print(f"Percentil 75:           {gdf_validos[indice].quantile(0.75):.4f}")
    
    # Guardar informe en archivo
    output_dir = Path('./informes')
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f'informe_{indice}_{timestamp}.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"INFORME ESTADÍSTICO: {indice}\n")
        f.write(f"{'='*60}\n\n")
        f.write(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Archivo fuente: {shapefile_path}\n\n")
        
        f.write("Distribución por clases:\n")
        f.write("-" * 60 + "\n")
        for clase, cantidad in distribucion.items():
            porcentaje = (cantidad / total_pixeles) * 100
            f.write(f"{clase:15s} | {cantidad:5d} píxeles ({porcentaje:5.1f}%)\n")
        
        f.write(f"\n{'='*60}\n")
        f.write("Estadísticas Generales:\n")
        f.write("-" * 60 + "\n")
        f.write(f"Total píxeles válidos:  {total_pixeles}\n")
        f.write(f"Mínimo:                 {gdf_validos[indice].min():.4f}\n")
        f.write(f"Máximo:                 {gdf_validos[indice].max():.4f}\n")
        f.write(f"Media:                  {gdf_validos[indice].mean():.4f}\n")
        f.write(f"Mediana:                {gdf_validos[indice].median():.4f}\n")
        f.write(f"Desviación estándar:    {gdf_validos[indice].std():.4f}\n")
    
    print(f"\n📄 Informe guardado: {output_file}")


def menu_principal():
    """
    Menú interactivo para visualizar índices
    """
    print("\n" + "="*60)
    print("SISTEMA DE VISUALIZACIÓN DE ÍNDICES DE VEGETACIÓN")
    print("="*60)
    print("\nOpciones disponibles:")
    print("  1. Visualizar NDVI")
    print("  2. Visualizar NDRE")
    print("  3. Visualizar MSAVI")
    print("  4. Visualizar RECI")
    print("  5. Visualizar NDMI")
    print("  6. Visualizar TODOS los índices")
    print("  7. Generar informe estadístico")
    print("  0. Salir")
    
    while True:
        try:
            opcion = input("\nSelecciona una opción (0-7): ").strip()
            
            if opcion == '0':
                print("\n👋 ¡Hasta luego!")
                break
            elif opcion == '1':
                visualizar_indice('NDVI')
            elif opcion == '2':
                visualizar_indice('NDRE')
            elif opcion == '3':
                visualizar_indice('MSAVI')
            elif opcion == '4':
                visualizar_indice('RECI')
            elif opcion == '5':
                visualizar_indice('NDMI')
            elif opcion == '6':
                visualizar_todos_indices()
            elif opcion == '7':
                print("\nÍndices disponibles:")
                print("  1. NDVI  2. NDRE  3. MSAVI  4. RECI  5. NDMI")
                idx = input("Selecciona índice para informe (1-5): ").strip()
                indices_map = {'1': 'NDVI', '2': 'NDRE', '3': 'MSAVI', '4': 'RECI', '5': 'NDMI'}
                if idx in indices_map:
                    generar_informe_estadistico(indices_map[idx])
                else:
                    print("❌ Opción inválida")
            else:
                print("❌ Opción inválida. Intenta de nuevo.")
        except KeyboardInterrupt:
            print("\n\n👋 Interrumpido por el usuario. ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("\n🎨 Sistema de Visualización de Índices de Vegetación")
    print("   Paletas de colores específicas para cada índice")
    print("   Sentinel-2 | NDVI, NDRE, MSAVI, RECI, NDMI\n")
    
    # Verificar que estamos en el directorio correcto
    if not Path('./descargas').exists():
        print("⚠️ Advertencia: No se encontró la carpeta 'descargas'")
        print("   Asegúrate de ejecutar este script desde el directorio raíz del proyecto")
    
    menu_principal()
