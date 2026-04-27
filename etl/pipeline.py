"""
Pipeline ETL principal — AgTech Datawarehouse

Orquesta la ejecución completa del pipeline:
  1. Extracción desde MongoDB y Redis
  2. Transformación y limpieza de datos
  3. Carga hacia Supabase/PostgreSQL

Uso:
    python etl/pipeline.py
"""

import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta

from extractors.mongodb_extractor import extract_sensor_readings
from extractors.redis_extractor import extract_realtime_state
from transformers.sensor_transformer import transform_readings
from loaders.supabase_loader import load_to_staging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()


def run_pipeline():
    """Ejecuta el pipeline ETL completo."""
    logger.info("Iniciando pipeline ETL...")

    # 1. Extracción
    logger.info("Paso 1: Extracción de datos")
    # Extraemos el último mes a modo de ejemplo
    hasta = datetime.now()
    desde = hasta - timedelta(days=30)
    
    # Extraer de MongoDB
    raw_mongo_data = extract_sensor_readings(desde, hasta)
    
    # Extraer de Redis (se puede usar para cruzar alertas o estados actuales)
    realtime_state = extract_realtime_state()

    # 2. Transformación
    logger.info("Paso 2: Transformación de datos")
    transformed_df = transform_readings(raw_mongo_data)

    # 3. Carga
    logger.info("Paso 3: Carga de datos")
    filas_cargadas = load_to_staging(transformed_df)
    
    logger.info(f"Pipeline ETL completado exitosamente. Filas cargadas/actualizadas: {filas_cargadas}")


if __name__ == "__main__":
    run_pipeline()
