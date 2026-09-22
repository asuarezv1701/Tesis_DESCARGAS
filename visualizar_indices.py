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

def obtener_areas_disponibles():
    """
    Obtiene las áreas disponibles en la carpeta de descargas
    
    Returns:
        list: Lista de nombres de áreas disponibles
    """
    base_dir = Path("descargas")
    if not base_dir.exists():
        return []
    
    areas = []
    for area_dir in base_dir.iterdir():
        if area_dir.is_dir():
            # Verificar si tiene al menos un índice con datos
            tiene_datos = False
            for indice_dir in area_dir.iterdir():
                if indice_dir.is_dir():
                    # Verificar si hay carpetas de descarga
                    if any(d.is_dir() for d in indice_dir.iterdir()):
                        tiene_datos = True
                        break
            
            if tiene_datos:
                areas.append(area_dir.name)
    
    return areas

def seleccionar_area():
    """
    Permite al usuario seleccionar un área disponible
    
    Returns:
        str: Nombre del área seleccionada o None si no hay áreas
    """
    areas = obtener_areas_disponibles()
    
    if not areas:
        print("⚠️ No se encontraron áreas con datos")
        return None
    
    if len(areas) == 1:
        print(f"Área detectada: {areas[0]}")
        return areas[0]
    
    print("Áreas disponibles:")
    for i, area in enumerate(areas, 1):
        print(f"  {i}. {area}")
    
    while True:
        try:
            seleccion = input(f"Selecciona área (1-{len(areas)}): ").strip()
            idx = int(seleccion) - 1
            if 0 <= idx < len(areas):
                return areas[idx]
            else:
                print(f"Por favor selecciona un número entre 1 y {len(areas)}")
        except ValueError:
            print("Por favor ingresa un número válido")

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


def encontrar_archivo_mas_reciente(indice, area):
    """
    Encuentra el shapefile más reciente para un índice y área específicos
    
    Args:
        indice: Nombre del índice (NDVI, NDRE, MSAVI, RECI, NDMI)
        area: Nombre del área
    
    Returns:
        Path del shapefile o None si no se encuentra
    """
    ruta_descargas = Path('./descargas') / area / indice
    
    if not ruta_descargas.exists():
        print(f"⚠️ No se encontraron shapefiles en: {ruta_descargas}")
        return None
    
    # Buscar todos los shapefiles de píxeles extraídos
    shapefiles = list(ruta_descargas.rglob(f'pixeles_{indice}_*.shp'))
    
    if not shapefiles:
        print(f"⚠️ No se encontraron shapefiles en: {ruta_descargas}")
        return None
    
    # Obtener el más reciente por fecha de modificación
    shapefile_reciente = max(shapefiles, key=lambda p: p.stat().st_mtime)
    return shapefile_reciente


def visualizar_indice(indice, shapefile_path=None, guardar=True, area=None):
    """
    Visualiza un índice de vegetación con su paleta de colores específica
    
    Args:
        indice: Nombre del índice (NDVI, NDRE, MSAVI, RECI, NDMI)
        shapefile_path: Ruta al shapefile (opcional, busca automáticamente)
        guardar: Si True, guarda la imagen
        area: Nombre del área (requerido si no se especifica shapefile_path)
    """
    print(f"\n{'='*60}")
    print(f"Visualizando índice: {indice}")
    print(f"{'='*60}")
    
    # Buscar shapefile si no se proporciona
    if shapefile_path is None:
        if area is None:
            print("❌ Error: Debe especificar área o shapefile_path")
            return False
        shapefile_path = encontrar_archivo_mas_reciente(indice, area)
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
    
    # Cargar el polígono del área y filtrar solo píxeles dentro del polígono
    try:
        area_shapefile_dir = Path(f"shapefiles/{area}")
        if area_shapefile_dir.exists():
            shapefiles = list(area_shapefile_dir.glob("*.shp"))
            if shapefiles:
                shapefile_area = gpd.read_file(shapefiles[0])
                # Asegurar que ambos GeoDataFrames tengan el mismo CRS
                if gdf_validos.crs != shapefile_area.crs:
                    gdf_validos = gdf_validos.to_crs(shapefile_area.crs)
                # Filtrar solo puntos dentro del polígono
                gdf_validos = gpd.sjoin(gdf_validos, shapefile_area, predicate='within', how='inner')
                print(f"📍 Píxeles dentro del polígono: {len(gdf_validos)}")
    except Exception as e:
        print(f"⚠️ Advertencia: No se pudo filtrar por polígono: {e}")
    
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
    
    # Crear figura con fondo claro (legible en impresión de tesis)
    fig, ax = plt.subplots(figsize=(14, 12), facecolor='white')
    ax.set_facecolor('#F5F5F5')  # Gris muy claro para el área de ploteo

    # Plotear datos con puntos más grandes
    gdf_validos.plot(
        column=indice,
        ax=ax,
        cmap=cmap,
        norm=norm,
        edgecolor='#666666',    # Borde gris para definición sobre fondo claro
        linewidth=0.1,         # Línea muy fina
        legend=False,
        markersize=50,          # Puntos más grandes (era 20)
        alpha=0.95              # Más opacidad para mejor visibilidad
    )

    # Configurar título y etiquetas
    ax.set_title(config['titulo'], fontsize=18, fontweight='bold', pad=20, color='#2C3E50')
    ax.set_xlabel('Longitud', fontsize=12, color='#2C3E50')
    ax.set_ylabel('Latitud', fontsize=12, color='#2C3E50')

    # Configurar colores de los ticks
    ax.tick_params(colors='#2C3E50')

    # Agregar descripción
    ax.text(0.5, -0.08, config['descripcion'],
            transform=ax.transAxes,
            ha='center', fontsize=10, style='italic', color='#2C3E50',
            bbox=dict(boxstyle='round', facecolor='#ECF0F1', alpha=0.9, edgecolor='#BDC3C7'))

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
        shadow=True,
        facecolor='white',       # Fondo blanco para la leyenda
        edgecolor='#BDC3C7',     # Borde gris claro
        labelcolor='#2C3E50'     # Texto oscuro
    )
    # Color del título de la leyenda
    legend.get_title().set_color('#2C3E50')

    # Agregar información adicional
    info_text = f"Píxeles: {len(gdf_validos)}\n"
    info_text += f"Rango: {gdf_validos[indice].min():.3f} - {gdf_validos[indice].max():.3f}\n"
    info_text += f"Media: {gdf_validos[indice].mean():.3f}"

    ax.text(0.02, 0.98, info_text,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment='top',
            color='#2C3E50',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='#BDC3C7'))

    # Agregar fecha
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    ax.text(0.98, 0.02, f'Generado: {fecha_actual}',
            transform=ax.transAxes,
            fontsize=8,
            ha='right',
            va='bottom',
            style='italic',
            color='#7F8C8D')

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
    plt.close(fig)

    return True


def visualizar_todos_indices(area):
    """
    Visualiza todos los índices disponibles
    
    Args:
        area: Nombre del área seleccionada
    """
    print("\n" + "="*60)
    print("VISUALIZACIÓN DE TODOS LOS ÍNDICES DE VEGETACIÓN")
    print("="*60)
    
    indices = ['NDVI', 'NDRE', 'MSAVI', 'RECI', 'NDMI']
    resultados = []
    
    for indice in indices:
        exito = visualizar_indice(indice, area=area)
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


def generar_informe_estadistico(indice, area):
    """
    Genera un informe estadístico detallado para un índice
    
    Args:
        indice: Nombre del índice (NDVI, NDRE, MSAVI, RECI, NDMI)
        area: Nombre del área seleccionada
    """
    shapefile_path = encontrar_archivo_mas_reciente(indice, area)
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


def menu_principal(area):
    """
    Menú interactivo para visualizar índices
    
    Args:
        area: Nombre del área seleccionada
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
                visualizar_indice('NDVI', area=area)
            elif opcion == '2':
                visualizar_indice('NDRE', area=area)
            elif opcion == '3':
                visualizar_indice('MSAVI', area=area)
            elif opcion == '4':
                visualizar_indice('RECI', area=area)
            elif opcion == '5':
                visualizar_indice('NDMI', area=area)
            elif opcion == '6':
                visualizar_todos_indices(area)
            elif opcion == '7':
                print("\nÍndices disponibles:")
                print("  1. NDVI  2. NDRE  3. MSAVI  4. RECI  5. NDMI")
                idx = input("Selecciona índice para informe (1-5): ").strip()
                indices_map = {'1': 'NDVI', '2': 'NDRE', '3': 'MSAVI', '4': 'RECI', '5': 'NDMI'}
                if idx in indices_map:
                    generar_informe_estadistico(indices_map[idx], area)
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
        sys.exit(1)
    
    # Seleccionar área
    area_seleccionada = seleccionar_area()
    if not area_seleccionada:
        print("❌ No hay áreas disponibles para visualizar")
        sys.exit(1)
    
    print(f"\n📍 Trabajando con área: {area_seleccionada}\n")
    
    menu_principal(area_seleccionada)
