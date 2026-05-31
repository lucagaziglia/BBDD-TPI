import os
import logging
import pandas as pd
from supabase import create_client

logger = logging.getLogger(__name__)

def load_to_mediciones_diarias(df: pd.DataFrame) -> int:
    if df.empty:
        logger.info("DataFrame vacío, nada para cargar.")
        return 0

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        logger.error("Faltan credenciales de Supabase. Abortando carga.")
        return 0

    supabase = create_client(url, key)
    
    # Convertir el DataFrame a una lista de diccionarios (registros)
    # Se convierte la fecha a string para que sea compatible con JSON/PostgreSQL
    df['fecha'] = df['fecha'].astype(str)
    records = df.to_dict(orient="records")

    try:
        # UPSERT con lote_id y fecha 
        response = supabase.table("dim_mediciones_diarias").upsert(
            records, on_conflict="lote_id, fecha"
        ).execute()
        
        return len(response.data)
    except Exception as e:
        logger.error(f"Error al cargar en Supabase: {e}")
        return 0
