"""
Módulo central de procesamiento de datos satelitales.
Maneja el cálculo de índices de vegetación y validación de datos.
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from dataclasses import dataclass


@dataclass
class VegetationIndex:
    """Representa un índice de vegetación con sus metadatos"""
    name: str
    description: str
    formula: str
    valid_range: tuple


class VegetationIndicesProcessor:
    """Procesa índices de vegetación a partir de datos Sentinel-2"""
    
    # Define índices soportados con sus metadatos
    INDICES_METADATA = {
        'NDVI': VegetationIndex(
            name='NDVI',
            description='Índice de Vegetación de Diferencia Normalizada',
            formula='(NIR - ROJO) / (NIR + ROJO)',
            valid_range=(-1.0, 1.0)
        ),
        'NDRE': VegetationIndex(
            name='NDRE', 
            description='Índice del Borde Rojo de Diferencia Normalizada',
            formula='(NIR - BORDE_ROJO) / (NIR + BORDE_ROJO)',
            valid_range=(-1.0, 1.0)
        ),
        'MSAVI': VegetationIndex(
            name='MSAVI',
            description='Índice de Vegetación Ajustado al Suelo Modificado',
            formula='(2*NIR + 1 - sqrt((2*NIR + 1)^2 - 8*(NIR - ROJO))) / 2',
            valid_range=(-1.0, 1.0)
        ),
        'RECI': VegetationIndex(
            name='RECI',
            description='Índice de Clorofila del Borde Rojo',
            formula='(NIR / BORDE_ROJO) - 1',
            valid_range=(-10.0, 20.0)
        ),
        'NDMI': VegetationIndex(
            name='NDMI',
            description='Índice de Humedad de Diferencia Normalizada',
            formula='(NIR - SWIR) / (NIR + SWIR)',
            valid_range=(-1.0, 1.0)
        )
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    @staticmethod
    def get_evalscript() -> str:
        """Retorna el evalscript para la API de Sentinel Hub"""
        return """
//VERSION=3
function setup() {
  return {
    input: ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "dataMask"],
    output: { 
      bands: 6,
      sampleType: "FLOAT32"
    }
  };
}

function evaluatePixel(sample) {
    // NDVI - Indice de Vegetacion de Diferencia Normalizada
    let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
    
    // NDRE - Indice del Borde Rojo de Diferencia Normalizada
    let ndre = (sample.B08 - sample.B05) / (sample.B08 + sample.B05);
    
    // MSAVI - Indice de Vegetacion Ajustado al Suelo Modificado
    let msavi = (2 * sample.B08 + 1 - Math.sqrt(Math.pow((2 * sample.B08 + 1), 2) - 8 * (sample.B08 - sample.B04))) / 2;
    
    // RECI - Indice de Clorofila del Borde Rojo
    let reci = (sample.B08 / sample.B05) - 1;
    
    // NDMI - Indice de Humedad de Diferencia Normalizada
    let ndmi = (sample.B08 - sample.B11) / (sample.B08 + sample.B11);
    
    // Meta-indice (promedio de NDVI y NDRE)
    let metaindice = (ndvi + ndre) / 2;
    
    return [ndvi, ndre, msavi, reci, ndmi, metaindice];
}
"""
    
    def validate_band_data(self, data: np.ndarray, band_name: str) -> bool:
        """Valida datos de banda individual"""
        if data is None or data.size == 0:
            self.logger.error(f"Datos vacíos para la banda {band_name}")
            return False
            
        if band_name in self.INDICES_METADATA:
            valid_range = self.INDICES_METADATA[band_name].valid_range
            if np.any(data < valid_range[0]) or np.any(data > valid_range[1]):
                self.logger.warning(f"La banda {band_name} contiene valores fuera del rango esperado {valid_range}")
                
        return True
        
    def get_band_names(self) -> List[str]:
        """Obtiene lista de nombres de bandas de salida"""
        return ["NDVI", "NDRE", "MSAVI", "RECI", "NDMI", "Meta-Indice"]
        
    def get_band_descriptions(self) -> List[str]:
        """Obtiene descripciones detalladas para cada banda"""
        band_names = self.get_band_names()
        descriptions = []
        
        for name in band_names:
            if name == "Meta-Indice":
                descriptions.append("Meta-índice: Promedio de NDVI y NDRE")
            elif name in self.INDICES_METADATA:
                descriptions.append(f"{name}: {self.INDICES_METADATA[name].description}")
            else:
                descriptions.append(f"{name}: Índice de vegetación")
                
        return descriptions
        
    def validate_output_data(self, data: List[np.ndarray]) -> bool:
        """Valida los datos completos de salida"""
        if not data or len(data) == 0:
            self.logger.error("No hay datos de salida para validar")
            return False
            
        expected_bands = len(self.get_band_names())
        if len(data) != expected_bands:
            self.logger.error(f"Se esperaban {expected_bands} bandas, se obtuvieron {len(data)}")
            return False
            
        # Validar cada banda
        band_names = self.get_band_names()
        for i, band_data in enumerate(data):
            if not self.validate_band_data(band_data, band_names[i]):
                return False
                
        self.logger.info(f"Se validaron exitosamente {len(data)} bandas de índices de vegetación")
        return True