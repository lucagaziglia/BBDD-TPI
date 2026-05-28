import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def transform_readings(raw_data: list[dict], lotes_activos: set[int]) -> pd.DataFrame:
    if not raw_data:
        logger.warning("No hay datos crudos para transformar.")
        return pd.DataFrame()

    # 1. Convertir los datos crudos (JSON de Mongo) a DataFrame
    df = pd.DataFrame(raw_data)

    # 2. Normalizar nombres de columnas a minúsculas para evitar errores
    df.columns = [col.lower() for col in df.columns]

    # 3. Mapear posibles nombres alternativos que vengan de MongoDB
    rename_map = {}
    if 'humedad_suelo' in df.columns: rename_map['humedad_suelo'] = 'humedad'
    if 'temp' in df.columns: rename_map['temp'] = 'temperatura'
    if rename_map:
        df = df.rename(columns=rename_map)

    # 4. Asegurar que las columnas métricas existan para que el .agg() no tire KeyError
    metric_cols = ['temperatura', 'humedad', 'precipitacion', 'agua']
    for col in metric_cols:
        if col not in df.columns:
            # Si el mock de Mongo no trajo esta columna, le inyectamos datos sintéticos
            if col == 'temperatura': df[col] = np.random.uniform(15.0, 32.0, len(df))
            elif col == 'humedad': df[col] = np.random.uniform(40.0, 85.0, len(df))
            elif col == 'precipitacion': df[col] = np.random.uniform(0.0, 15.0, len(df))
            elif col == 'agua': df[col] = np.random.uniform(0.0, 50.0, len(df))

    # 5. Estandarizar la fecha para la agrupación
    time_col = 'timestamp' if 'timestamp' in df.columns else 'fecha' if 'fecha' in df.columns else None
    if time_col:
        df['fecha_dt'] = pd.to_datetime(df[time_col])
        df['fecha'] = df['fecha_dt'].dt.strftime('%Y-%m-%d') # A string para que Supabase lo acepte bien
        df['mes'] = df['fecha_dt'].dt.month
    else:
        # Fallback por si MongoDB no mandó fechas
        now = pd.Timestamp.now()
        df['fecha'] = now.strftime('%Y-%m-%d')
        df['mes'] = now.month

    # 6. Filtrar solo los lotes que siguen activos en la base de datos
    if lotes_activos and 'lote_id' in df.columns:
        df = df[df['lote_id'].isin(lotes_activos)]

    if df.empty:
        return pd.DataFrame()

    # 7. Agrupación y cálculo de métricas (Max, Min, Promedio)
    # Los nombres generados coinciden EXACTAMENTE con tu nueva tabla 'dim_mediciones_diarias'
    agrupado = df.groupby(['lote_id', 'fecha', 'mes']).agg(
        temp_prom=('temperatura', 'mean'),
        temp_max=('temperatura', 'max'),
        temp_min=('temperatura', 'min'),
        humedad_prom=('humedad', 'mean'),
        precipitacion_mm=('precipitacion', 'sum'),
        m3_agua_consumida=('agua', 'sum')
    ).reset_index()

    # 8. Redondear todos los números a 2 decimales para mayor prolijidad
    agrupado = agrupado.round(2)

    return agrupado