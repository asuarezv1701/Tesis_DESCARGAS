"""
SCRIPT MAESTRO - Proceso Completo Sentinel-2
Descarga → Extrae → Visualiza
"""

import subprocess
import sys

# Colores
class C:
    G = '\033[92m'; Y = '\033[93m'; R = '\033[91m'; B = '\033[94m'; E = '\033[0m'

def ejecutar_script(nombre_archivo, descripcion):
    """Ejecuta un script Python y maneja errores"""
    print(f"\n{C.B}{'='*70}")
    print(f"  {descripcion}")
    print(f"{'='*70}{C.E}\n")
    
    try:
        resultado = subprocess.run([sys.executable, nombre_archivo], check=True)
        print(f"\n{C.G}✓ {descripcion} completado{C.E}\n")
        return True
    except subprocess.CalledProcessError:
        print(f"\n{C.R}✗ Error en {descripcion}{C.E}")
        return False
    except KeyboardInterrupt:
        print(f"\n{C.Y}⚠ Proceso interrumpido por el usuario{C.E}")
        return False

print(f"\n{C.B}{'='*70}")
print("   SISTEMA COMPLETO SENTINEL-2")
print("   Descarga → Extracción → Visualización")
print(f"{'='*70}{C.E}\n")

print(f"{C.Y}Este proceso ejecutará:{C.E}")
print("  1. Descarga de imágenes Sentinel-2")
print("  2. Extracción de valores de píxeles")
print("  3. Visualización de índices")
print()

continuar = ''
while continuar not in ['s', 'n']:
    continuar = input(f"{C.Y}¿Deseas continuar? (s/n): {C.E}").strip().lower()
    if continuar not in ['s', 'n']:
        print(f"{C.R}✗ Respuesta inválida. Ingresa 's' para Sí o 'n' para No.{C.E}")

if continuar != 's':
    print(f"{C.R}✗ Proceso cancelado{C.E}")
    sys.exit(0)

# PASO 1: Descarga
if not ejecutar_script("descargar_simple.py", "PASO 1: DESCARGA DE IMÁGENES"):
    print(f"{C.R}✗ Proceso detenido por error en descarga{C.E}")
    sys.exit(1)

# PASO 2: Extracción
continuar = ''
while continuar not in ['s', 'n']:
    continuar = input(f"\n{C.Y}¿Continuar con la extracción de píxeles? (s/n): {C.E}").strip().lower()
    if continuar not in ['s', 'n']:
        print(f"{C.R}✗ Respuesta inválida. Ingresa 's' para Sí o 'n' para No.{C.E}")

if continuar != 's':
    print(f"{C.Y}⚠ Proceso detenido. Las descargas están disponibles en descargas/{C.E}")
    sys.exit(0)

if not ejecutar_script("extraer_pixeles.py", "PASO 2: EXTRACCIÓN DE PÍXELES"):
    print(f"{C.R}✗ Proceso detenido por error en extracción{C.E}")
    sys.exit(1)

# PASO 3: Visualización
continuar = ''
while continuar not in ['s', 'n']:
    continuar = input(f"\n{C.Y}¿Continuar con la visualización? (s/n): {C.E}").strip().lower()
    if continuar not in ['s', 'n']:
        print(f"{C.R}✗ Respuesta inválida. Ingresa 's' para Sí o 'n' para No.{C.E}")

if continuar != 's':
    print(f"{C.Y}⚠ Proceso detenido. Los datos están en descargas/ y CSV/Shapefiles generados{C.E}")
    sys.exit(0)

if not ejecutar_script("visualizar_indices.py", "PASO 3: VISUALIZACIÓN DE ÍNDICES"):
    print(f"{C.R}✗ Error en visualización{C.E}")
    sys.exit(1)

print(f"\n{C.B}{'='*70}")
print("   ✓ PROCESO COMPLETO FINALIZADO")
print(f"{'='*70}{C.E}\n")
print(f"{C.G}✓ Descargas en: descargas/{C.E}")
print(f"{C.G}✓ CSV/Shapefiles generados en cada carpeta{C.E}")
print(f"{C.G}✓ Visualizaciones generadas{C.E}\n")
