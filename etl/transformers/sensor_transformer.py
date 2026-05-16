import pandas as pd
import logging

logger = logging.getLogger(__name__)

def transform_readings(raw_data: list[dict], lotes_activos: set[int]) -> pd.DataFrame:
    if not raw_data:
        logger.warning("No hay datos crudos para transformar.")
        return pd.DataFrame()

    df = pd.DataFrame(raw_data)

    # Filtrar solo los lotes que siguen activos
    if lotes_activos:
        df = df[df['lote_id'].isin(lotes_activos)]

    if df.empty:
        return pd.DataFrame()

    # Asegurar formato de fecha y extraer las nuevas columnas requeridas
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['fecha'] = df['timestamp'].dt.date
    df['mes'] = df['timestamp'].dt.month

    # Filtrar outliers (ejemplo de lógica de negocio)
    # df = df[(df['temperatura'] >= -10) & (df['temperatura'] <= 50)]

    # Agrupar por lote y por la fecha exacta (la nueva clave)
    agrupado = df.groupby(['lote_id', 'fecha', 'mes']).agg(
        temp_prom=('temperatura', 'mean'),
        temp_max=('temperatura', 'max'),
        temp_min=('temperatura', 'min'),
        humedad_prom=('humedad', 'mean'),
        precipitacion_mm=('precipitacion', 'sum'),
        m3_agua_consumida=('agua', 'sum')
    ).reset_index()

    # Redondear a 2 decimales para la base de datos
    agrupado = agrupado.round(2)

    return agrupado