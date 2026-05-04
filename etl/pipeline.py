import sys
import os
import logging
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from extractors.mongodb_extractor import extract_sensor_readings
from extractors.redis_extractor import extract_realtime_state
from transformers.sensor_transformer import transform_readings
from loaders.supabase_loader import load_to_dim_clima

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()


def fetch_tiempo_map() -> dict[date, int]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        logger.warning("Sin credenciales Supabase — mapeo fecha→tiempo_id no disponible.")
        return {}

    try:
        from supabase import create_client
        client = create_client(url, key)
        rows = (
            client.table("dim_tiempo")
            .select("tiempo_id, fecha")
            .execute()
            .data
        )
        mapping: dict[date, int] = {}
        for r in rows:
            f = r["fecha"]
            if isinstance(f, str):
                f = date.fromisoformat(f)
            mapping[f] = r["tiempo_id"]
        logger.info(f"Mapeo fecha→tiempo_id cargado: {len(mapping)} entradas.")
        return mapping
    except Exception as e:
        logger.warning(f"No se pudo cargar mapeo fecha→tiempo_id: {e}")
        return {}


def fetch_lotes_activos() -> set[int]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        logger.warning("Sin credenciales Supabase — validación de lotes activos no disponible.")
        return set()

    try:
        from supabase import create_client
        client = create_client(url, key)
        rows = (
            client.table("dim_lote")
            .select("lote_id")
            .eq("activo", True)
            .execute()
            .data
        )
        lotes = {r["lote_id"] for r in rows}
        logger.info(f"Lotes activos en dim_lote: {len(lotes)}.")
        return lotes
    except Exception as e:
        logger.warning(f"No se pudo cargar lotes activos: {e}")
        return set()


def run_pipeline(dias: int = 30) -> dict:
    resultados = {"filas_extraidas": 0, "filas_transformadas": 0, "filas_cargadas": 0}
    inicio = datetime.now()
    logger.info(f"=== Iniciando pipeline ETL (últimos {dias} días) ===")

    tiempo_map    = fetch_tiempo_map()
    lotes_activos = fetch_lotes_activos()

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

    logger.info("PASO 2/3 — Transform")
    df_transformado = transform_readings(
        raw_mongo,
        tiempo_map=tiempo_map,
        lotes_activos=lotes_activos,
    )
    resultados["filas_transformadas"] = len(df_transformado)

    if df_transformado.empty:
        logger.warning("Transform produjo DataFrame vacío. Abortando carga.")
        return resultados

    logger.info("PASO 3/3 — Load")
    filas_cargadas = load_to_dim_clima(df_transformado)
    resultados["filas_cargadas"] = filas_cargadas

    duracion = (datetime.now() - inicio).total_seconds()
    logger.info(f"=== Pipeline completado en {duracion:.1f}s ===")
    logger.info(f"    Extraídos:    {resultados['filas_extraidas']} documentos MongoDB")
    logger.info(f"    Transformados:{resultados['filas_transformadas']} filas")
    logger.info(f"    Cargados:     {resultados['filas_cargadas']} filas en dim_clima")
    return resultados


if __name__ == "__main__":
    run_pipeline()
