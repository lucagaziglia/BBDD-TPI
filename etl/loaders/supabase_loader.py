"""
Loader para Supabase (PostgreSQL).

ETL — Fase LOAD:
Inserta o actualiza los datos transformados en la tabla dim_clima
del Datawarehouse usando UPSERT vía supabase-py (REST API).

El UPSERT garantiza idempotencia: correr el pipeline dos veces
sobre el mismo período no duplica datos.
"""
import os
import logging
import pandas as pd
from supabase import create_client

logger = logging.getLogger(__name__)


def load_to_dim_clima(df: pd.DataFrame) -> int:
    """
    Carga el DataFrame transformado en la tabla dim_clima de Supabase.

    Usa UPSERT: si ya existe una fila para (localidad_id, fecha), la actualiza.
    Si no existe, la inserta. Esto hace el pipeline idempotente.

    Args:
        df: DataFrame con columnas localidad_id, fecha, temp_promedio,
            temp_max, temp_min, humedad_promedio.

    Returns:
        Cantidad de filas insertadas o actualizadas.
    """
    if df.empty:
        logger.info("DataFrame vacío, nada para cargar.")
        return 0

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        logger.warning("SUPABASE_URL o SUPABASE_KEY no configuradas — simulando carga (modo dry-run).")
        logger.info(f"[DRY-RUN] Se cargarían {len(df)} filas a dim_clima.")
        return len(df)

    def safe_float(val):
        if pd.isna(val):
            return None
        return round(float(val), 4)

    records = [
        {
            "localidad_id":    int(row["localidad_id"]),
            "fecha":           str(row["fecha"]),
            "temp_promedio":   safe_float(row.get("temp_promedio")),
            "temp_max":        safe_float(row.get("temp_max")),
            "temp_min":        safe_float(row.get("temp_min")),
            "humedad_promedio":safe_float(row.get("humedad_promedio")),
        }
        for _, row in df.iterrows()
    ]

    try:
        client = create_client(url, key)
        resp = (
            client.table("dim_clima")
            .upsert(records, on_conflict="localidad_id,fecha")
            .execute()
        )
        filas = len(resp.data) if resp.data else 0
        logger.info(f"Carga completada: {filas} filas en dim_clima.")
        return filas

    except Exception as e:
        logger.error(f"Error cargando en Supabase: {e}")
        return 0


# Mantener compatibilidad con el nombre anterior usado en pipeline.py
load_to_staging = load_to_dim_clima
