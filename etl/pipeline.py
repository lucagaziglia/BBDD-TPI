"""
Pipeline ETL: Cassandra → Extract →  Transform → Load → Supabase.

"""
import sys
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv

# Cargar .env desde la raíz del proyecto
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from extractors.cassandra_extractor import (
    extract_sensor_readings,
    extract_realtime_state,
    connect_astradb,
)
from transformers.sensor_transformer import transform_readings
from loaders.supabase_loader import load_to_mediciones_diarias
from supabase import create_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger(__name__)


def fetch_lotes_activos() -> set[int]:
    """Trae los lotes activos desde Supabase para filtrar el proceso."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        logger.warning("Sin credenciales Supabase — validación de lotes activos no disponible (usando fallback).")
        return set(range(1, 26))

    try:
        supabase = create_client(url, key)
        response = supabase.table("dim_campo").select("campo_id").execute()
        ids = {row.get("lote_id") or row.get("campo_id") for row in response.data}
        logger.info(f"Validación: {len(ids)} lotes activos encontrados en la base.")
        return ids
    except Exception as e:
        logger.error(f"Error al validar lotes: {e}. Usando fallback.")
        return set(range(1, 26))


def run_pipeline(dias: int = 30) -> dict:
    resultados = {"filas_extraidas": 0, "filas_transformadas": 0, "filas_cargadas": 0}
    inicio = datetime.now()
    logger.info(f"=== Iniciando pipeline ETL (últimos {dias} días) ===")

    lotes_activos = fetch_lotes_activos()
    hasta = datetime.now()
    desde = hasta - timedelta(days=dias)

    # EXTRACCION histórico
    logger.info("EXTRACCIÓN del histórico de Cassandra")
    raw_readings = extract_sensor_readings(desde, hasta)
    resultados["filas_extraidas"] = len(raw_readings)


    logger.info("EXTRACCIÓN del real-time de Cassandra")
    realtime_state = extract_realtime_state()
    logger.info(f"Estado caliente: {len(realtime_state)} entradas activas.")

    # TRANSFORMACION

    logger.info("TRANSFORMACION")
    df_transformado = transform_readings(
        raw_data=raw_readings,
        lotes_activos=lotes_activos
    )
    resultados["filas_transformadas"] = len(df_transformado)

    #CARGA
    logger.info("CARGA")
    if not df_transformado.empty:
        cargadas = load_to_mediciones_diarias(df_transformado)
        resultados["filas_cargadas"] = cargadas
    else:
        logger.warning("No hay datos para cargar después de la transformación.")

    fin = datetime.now()
    logger.info(f"=== Pipeline finalizado en {fin - inicio} ===")
    logger.info(f"Resumen: {resultados}")
    return resultados


if __name__ == "__main__":
    run_pipeline()
