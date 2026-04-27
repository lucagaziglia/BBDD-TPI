"""
Pipeline ETL principal — AgTech Datawarehouse

ETL completo: MongoDB + Redis → transformación → Supabase.

Uso desde la raíz del repo:
    python etl/pipeline.py

Uso desde dentro de etl/:
    python pipeline.py
"""
import sys
import os
import logging
from datetime import datetime, timedelta

# Fix de path: permite correr el script desde la raíz del repo
# sin que Python pierda los imports relativos dentro de etl/
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from extractors.mongodb_extractor import extract_sensor_readings
from extractors.redis_extractor import extract_realtime_state
from transformers.sensor_transformer import transform_readings
from loaders.supabase_loader import load_to_staging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()


def fetch_lote_localidad_map() -> dict[int, int]:
    """
    Consulta Supabase para obtener el mapeo lote_id → localidad_id.

    Hace JOIN dim_lote → dim_campo para resolver la localidad de cada lote.
    Si falla la consulta, retorna dict vacío (el transformer usará lote_id
    como fallback de localidad_id).
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        logger.warning("Sin credenciales Supabase — mapeo lote→localidad no disponible.")
        return {}

    try:
        from supabase import create_client
        client = create_client(url, key)
        rows = (
            client.table("dim_lote")
            .select("id, dim_campo!inner(localidad_id)")
            .execute()
            .data
        )
        mapping = {r["id"]: r["dim_campo"]["localidad_id"] for r in rows}
        logger.info(f"Mapeo lote→localidad cargado: {len(mapping)} lotes.")
        return mapping
    except Exception as e:
        logger.warning(f"No se pudo cargar mapeo lote→localidad: {e}")
        return {}


def run_pipeline(dias: int = 30) -> dict:
    """
    Ejecuta el pipeline ETL completo.

    Args:
        dias: Cantidad de días hacia atrás a procesar. Default: 30.

    Returns:
        Dict con resultados: filas_extraidas, filas_transformadas, filas_cargadas.
    """
    resultados = {"filas_extraidas": 0, "filas_transformadas": 0, "filas_cargadas": 0}
    inicio = datetime.now()
    logger.info(f"=== Iniciando pipeline ETL (últimos {dias} días) ===")

    # ── LOOKUP: mapeo lote_id → localidad_id ─────────────────────────
    lote_localidad_map = fetch_lote_localidad_map()

    # ── PASO 1: EXTRACT ──────────────────────────────────────────────
    logger.info("PASO 1/3 — Extract")
    hasta = datetime.now()
    desde = hasta - timedelta(days=dias)

    raw_mongo = extract_sensor_readings(desde, hasta)
    realtime  = extract_realtime_state()

    resultados["filas_extraidas"] = len(raw_mongo)
    logger.info(f"MongoDB: {len(raw_mongo)} documentos | Redis: {len(realtime)} keys")

    if not raw_mongo:
        logger.warning("Sin datos de MongoDB. Abortando pipeline.")
        return resultados

    # ── PASO 2: TRANSFORM ────────────────────────────────────────────
    logger.info("PASO 2/3 — Transform")
    df_transformado = transform_readings(raw_mongo, lote_localidad_map=lote_localidad_map)
    resultados["filas_transformadas"] = len(df_transformado)

    if df_transformado.empty:
        logger.warning("Transform produjo DataFrame vacío. Abortando carga.")
        return resultados

    # ── PASO 3: LOAD ─────────────────────────────────────────────────
    logger.info("PASO 3/3 — Load")
    filas_cargadas = load_to_staging(df_transformado)
    resultados["filas_cargadas"] = filas_cargadas

    # ── RESUMEN ──────────────────────────────────────────────────────
    duracion = (datetime.now() - inicio).total_seconds()
    logger.info(f"=== Pipeline completado en {duracion:.1f}s ===")
    logger.info(f"    Extraídos:    {resultados['filas_extraidas']} documentos MongoDB")
    logger.info(f"    Transformados:{resultados['filas_transformadas']} filas")
    logger.info(f"    Cargados:     {resultados['filas_cargadas']} filas en dim_clima")
    return resultados


if __name__ == "__main__":
    run_pipeline()
