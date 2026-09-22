"""
Manifiesto de descargas por área.

Registra, por índice y periodo (YYYYMM), qué se ha descargado, para que:
  - la descarga completa de la base se haga una sola vez,
  - corridas posteriores solo bajen los periodos faltantes,
  - se puedan re-descargar periodos concretos (modo "reemplazar"),
  - el análisis sepa qué fechas debe recalcular tras un reemplazo.

Archivo: descargas/<area>/manifest.json
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

NOMBRE_MANIFIESTO = "manifest.json"
PATRON_FECHA = re.compile(r'_(\d{8})(?:_|$)')


def periodo_de_fecha(fecha_yyyymmdd: str) -> str:
    """'20220923' -> '202209'"""
    return fecha_yyyymmdd[:6]


def rango_fechas_periodo(periodo: str) -> tuple[str, str]:
    """
    Convierte un periodo YYYYMM al rango [inicio, fin) que usa GEE.
    '202209' -> ('2022-09-01', '2022-10-01')
    """
    anio, mes = int(periodo[:4]), int(periodo[4:6])
    inicio = datetime(anio, mes, 1)
    fin = datetime(anio + 1, 1, 1) if mes == 12 else datetime(anio, mes + 1, 1)
    return inicio.strftime("%Y-%m-%d"), fin.strftime("%Y-%m-%d")


def expandir_periodos(entrada: str) -> List[str]:
    """
    Acepta:
      - rango:  '202201-202608'
      - lista:  '202609,202601'
      - mezcla: '202201-202203,202609'
    Devuelve lista ordenada y sin duplicados de periodos YYYYMM.
    Lanza ValueError si el formato es inválido.
    """
    periodos: set[str] = set()
    for token in entrada.replace(" ", "").split(","):
        if not token:
            continue
        if "-" in token:
            ini, fin = token.split("-", 1)
            _validar_periodo(ini)
            _validar_periodo(fin)
            if ini > fin:
                raise ValueError(f"El periodo inicial {ini} es posterior al final {fin}")
            actual = ini
            while actual <= fin:
                periodos.add(actual)
                anio, mes = int(actual[:4]), int(actual[4:6])
                actual = f"{anio + 1}01" if mes == 12 else f"{anio}{mes + 1:02d}"
        else:
            _validar_periodo(token)
            periodos.add(token)
    if not periodos:
        raise ValueError("No se indicó ningún periodo")
    return sorted(periodos)


def _validar_periodo(p: str) -> None:
    if not re.fullmatch(r'\d{6}', p):
        raise ValueError(f"Periodo inválido: '{p}' (formato YYYYMM)")
    mes = int(p[4:6])
    if mes < 1 or mes > 12:
        raise ValueError(f"Mes inválido en periodo '{p}'")


class Manifiesto:
    """Manejo del manifest.json de un área."""

    def __init__(self, carpeta_area: Path):
        self.carpeta_area = Path(carpeta_area)
        self.ruta = self.carpeta_area / NOMBRE_MANIFIESTO
        self.datos: Dict = {
            "area": self.carpeta_area.name,
            "actualizado": None,
            "periodos": {},              # {indice: {periodo: {...}}}
            "pendientes_recalculo": {},  # {indice: [fechas YYYY-MM-DD]}
        }
        if self.ruta.exists():
            with open(self.ruta, "r", encoding="utf-8") as f:
                self.datos.update(json.load(f))

    # ------------------------------------------------------------------ IO
    def guardar(self) -> None:
        self.carpeta_area.mkdir(parents=True, exist_ok=True)
        self.datos["actualizado"] = datetime.now().isoformat(timespec="seconds")
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump(self.datos, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------ consultas
    def entrada(self, indice: str, periodo: str) -> Optional[Dict]:
        return self.datos["periodos"].get(indice, {}).get(periodo)

    def esta_completo(self, indice: str, periodo: str) -> bool:
        e = self.entrada(indice, periodo)
        return bool(e and e.get("estado") == "completo")

    # --------------------------------------------------------- escritura
    def registrar(self, indice: str, periodo: str, fechas: List[str],
                  exitosos: int, fallidos: int, reemplazo: bool = False) -> None:
        estado = "completo" if fallidos == 0 else "parcial"
        self.datos["periodos"].setdefault(indice, {})[periodo] = {
            "estado": estado,
            "imagenes": exitosos,
            "fallidas": fallidos,
            "fechas": sorted(set(fechas)),
            "descargado": datetime.now().isoformat(timespec="seconds"),
        }
        if reemplazo:
            pend = self.datos["pendientes_recalculo"].setdefault(indice, [])
            for f in fechas:
                iso = f"{f[:4]}-{f[4:6]}-{f[6:8]}"
                if iso not in pend:
                    pend.append(iso)
            pend.sort()

    def limpiar_pendientes(self, indice: str) -> None:
        self.datos["pendientes_recalculo"].pop(indice, None)

    # ------------------------------------------------- reconstrucción disco
    def reconstruir_desde_disco(self) -> int:
        """
        Escanea descargas/<area>/<indice>/*/*.tiff y registra como 'completo'
        cada periodo que tenga al menos una imagen y no esté ya en el manifiesto.
        Devuelve cuántos (indice, periodo) se agregaron.
        Útil para adoptar una base descargada antes de existir el manifiesto.
        """
        agregados = 0
        if not self.carpeta_area.exists():
            return 0
        for carpeta_indice in sorted(self.carpeta_area.iterdir()):
            if not carpeta_indice.is_dir():
                continue
            indice = carpeta_indice.name
            por_periodo: Dict[str, List[str]] = {}
            for tiff in carpeta_indice.glob("*/*.tif*"):
                m = PATRON_FECHA.search(tiff.parent.name)
                if not m:
                    continue
                fecha = m.group(1)
                por_periodo.setdefault(periodo_de_fecha(fecha), []).append(fecha)
            for periodo, fechas in por_periodo.items():
                if self.entrada(indice, periodo) is None:
                    self.datos["periodos"].setdefault(indice, {})[periodo] = {
                        "estado": "completo",
                        "imagenes": len(fechas),
                        "fallidas": 0,
                        "fechas": sorted(set(fechas)),
                        "descargado": None,
                        "origen": "reconstruido",
                    }
                    agregados += 1
        return agregados


# ---------------------------------------------------------------- disco
def carpetas_de_periodo(carpeta_indice: Path, periodo: str) -> List[Path]:
    """Carpetas de imagen de un índice cuya fecha cae en el periodo dado."""
    resultado = []
    if not carpeta_indice.exists():
        return resultado
    for carpeta in carpeta_indice.iterdir():
        if not carpeta.is_dir():
            continue
        m = PATRON_FECHA.search(carpeta.name)
        if m and periodo_de_fecha(m.group(1)) == periodo:
            resultado.append(carpeta)
    return sorted(resultado)


PATRON_LEGADO = re.compile(r'_\d{8}_\d{8}_\d{6}$')  # area_YYYYMMDD_YYYYMMDD_HHMMSS


def existe_imagen(carpeta_indice: Path, fecha: str, tile: Optional[str] = None) -> bool:
    """
    ¿Ya hay un TIFF descargado para esa fecha (y tile, si se indica)?
    - Carpeta nueva  (area_YYYYMMDD_<tile>): coincide solo si el tile es el mismo.
    - Carpeta antigua (area_YYYYMMDD_<timestamp>): no registra tile, así que se
      considera existente para cualquier tile de esa fecha.
    """
    if not carpeta_indice.exists():
        return False
    for carpeta in carpeta_indice.glob(f"*_{fecha}_*"):
        if not carpeta.is_dir() or not any(carpeta.glob("*.tif*")):
            continue
        es_legado = bool(PATRON_LEGADO.search(carpeta.name))
        if tile is None or es_legado or carpeta.name.endswith(f"_{tile}"):
            return True
    return False
