# Script para activar el ambiente virtual y verificar dependencias
# Uso: .\activar_entorno.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Activando Ambiente Virtual - Tesis" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navegar al directorio del proyecto
Set-Location $PSScriptRoot

# Verificar si existe el ambiente virtual
if (-Not (Test-Path ".\.venv")) {
    Write-Host "ERROR: No se encontro el ambiente virtual .venv" -ForegroundColor Red
    Write-Host "Ejecuta: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Permitir ejecución de scripts (solo para esta sesión)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

# Activar ambiente virtual
Write-Host "Activando ambiente virtual..." -ForegroundColor Green
& ".\.venv\Scripts\Activate.ps1"

# Verificar activación
if ($env:VIRTUAL_ENV) {
    Write-Host "✓ Ambiente virtual activado correctamente" -ForegroundColor Green
    Write-Host "  Ruta: $env:VIRTUAL_ENV" -ForegroundColor Gray
} else {
    Write-Host "ERROR: No se pudo activar el ambiente virtual" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Verificando dependencias clave..." -ForegroundColor Yellow

# Verificar importaciones críticas
$verificacion = python -c "
try:
    import rasterio
    import fiona
    import geopandas
    import ee
    import geemap
    print('OK')
except ImportError as e:
    print(f'ERROR: {e}')
    exit(1)
" 2>&1

if ($verificacion -eq "OK") {
    Write-Host "✓ Todas las dependencias están instaladas" -ForegroundColor Green
} else {
    Write-Host "ERROR en dependencias:" -ForegroundColor Red
    Write-Host $verificacion -ForegroundColor Red
    Write-Host ""
    Write-Host "Ejecuta: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Ambiente listo para trabajar" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para desactivar el ambiente: deactivate" -ForegroundColor Gray
Write-Host ""
