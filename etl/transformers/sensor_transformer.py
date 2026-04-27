"""
Transformador de lecturas de sensores.
Utiliza pandas para agregar las lecturas crudas y calcular promedios diarios,
limpiando outliers y estandarizando formatos.
"""
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def transform_readings(raw_data: list[dict]) -> pd.DataFrame:
    """
    Limpia y estandariza las lecturas crudas de sensores.
    Agrupa por lote y fecha para obtener el promedio diario.
    """
    if not raw_data:
        logger.warning("No hay datos crudos para transformar.")
        return pd.DataFrame()
        
    logger.info("Transformando datos con pandas...")
    df = pd.DataFrame(raw_data)
    
    # 1. Normalización de fechas
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["fecha"] = df["timestamp"].dt.date
    
    # 2. Limpieza de Outliers (ej. humedad entre 0 y 100%)
    if "valor" in df.columns:
        df = df[(df["valor"] >= 0) & (df["valor"] <= 100)]
    
    # 3. Agregación: Promedio diario por métrica
    grouped = df.groupby(["lote_id", "fecha", "tipo_lectura"])["valor"].mean().reset_index()
    
    # 4. Pivot: Formato tabular (una columna por métrica)
    pivoted = grouped.pivot(index=["lote_id", "fecha"], columns="tipo_lectura", values="valor").reset_index()
    
    # Rellenar nulos con 0 u otro valor default
    pivoted = pivoted.fillna(0)
    
    logger.info(f"Transformación completa. {len(pivoted)} filas resultantes.")
    return pivoted
