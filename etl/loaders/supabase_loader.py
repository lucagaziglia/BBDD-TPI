import os
import logging
import pandas as pd
from supabase import create_client

logger = logging.getLogger(__name__)


def load_to_dim_clima(df: pd.DataFrame) -> int:
    if df.empty:
        logger.info("DataFrame vacío, nada para cargar.")
        return 0

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        logger.warning(
            "SUPABASE_URL o SUPABASE_KEY no configuradas — "
            "simulando carga (modo dry-run)."
        )
        logger.info(f"[DRY-RUN] Se cargarían {len(df)} filas a dim_clima.")
        return len(df)

    def safe_float(val):
        if pd.isna(val):
            return None
        return round(float(val), 4)

    records = [
        {
            "lote_id":          int(row["lote_id"]),
            "tiempo_id":        int(row["tiempo_id"]),
            "temp_promedio":    safe_float(row.get("temp_promedio")),
            "temp_max":         safe_float(row.get("temp_max")),
            "temp_min":         safe_float(row.get("temp_min")),
            "humedad_promedio": safe_float(row.get("humedad_promedio")),
            "precipitacion_mm": safe_float(row.get("precipitacion_mm")),
        }
        for _, row in df.iterrows()
    ]

    try:
        client = create_client(url, key)

        max_row = client.table("dim_clima").select("clima_id").order("clima_id", desc=True).limit(1).execute().data
        next_id = (max_row[0]["clima_id"] + 1) if max_row else 1

        lote_ids   = list({r["lote_id"]   for r in records})
        tiempo_ids = list({r["tiempo_id"] for r in records})
        client.table("dim_clima") \
              .delete() \
              .in_("lote_id",   lote_ids) \
              .in_("tiempo_id", tiempo_ids) \
              .execute()

        for i, r in enumerate(records):
            r["clima_id"] = next_id + i

        resp = client.table("dim_clima").insert(records).execute()
        filas = len(resp.data) if resp.data else 0
        logger.info(f"Carga completada: {filas} filas en dim_clima.")
        return filas

    except Exception as e:
        logger.error(f"Error cargando en Supabase: {e}")
        return 0


load_to_staging = load_to_dim_clima
