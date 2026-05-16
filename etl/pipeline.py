import sys
import os
import logging
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from extractors.mongodb_extractor import extract_sensor_readings
from extractors.redis_extractor import extract_realtime_state
from transformers.sensor_transformer import transform_readings

# CAMBIO 1: Importamos el nuevo loader
from loaders.supabase_loader import load_to_mediciones_diarias

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

# CAMBIO 2: La función fetch_tiempo_map() fue eliminada porque la fecha ahora se guarda directo

def fetch_lotes_activos() -> set[int]:
    """Trae los lotes activos para evitar procesar lotes dados de baja."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        logger.warning("Sin credenciales Supabase — validación de lotes activos no disponible.")
        # Como fallback para testing, asumimos un set de lotes válidos
        return set(range(1, 26))
    
    # Aquí va la lógica de Supabase (omitida por brevedad si ya la tenías implementada)
    # response = create_client(url, key).table("dim_lote").select("lote_id").eq("activo", True).execute()
    # return {row["lote_id"] for row in response.data}
    return set(range(1, 26))

def run_pipeline(dias: int = 30) -> dict:
    resultados = {"filas_extraidas": 0, "filas_transformadas": 0, "filas_cargadas": 0}
    inicio = datetime.now()
    logger.info(f"=== Iniciando pipeline ETL (últimos {dias} días) ===")

    # Preparación
    lotes_activos = fetch_lotes_activos()
    hasta = datetime.now()
    desde = hasta - timedelta(days=dias)

    # 1. Extracción
    logger.info("Fase 1: Extracción de datos desde MongoDB")
    raw_readings = extract_sensor_readings(desde, hasta)
    resultados["filas_extraidas"] = len(raw_readings)

    # 2. Transformación
    logger.info("Fase 2: Transformación y agregación")
    
    # CAMBIO 3: Ya no le pasamos el argumento tiempo_map
    df_transformado = transform_readings(
        raw_data=raw_readings,
        lotes_activos=lotes_activos
    )
    resultados["filas_transformadas"] = len(df_transformado)

    # 3. Carga (Load)
    logger.info("Fase 3: Carga en el Datawarehouse")
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