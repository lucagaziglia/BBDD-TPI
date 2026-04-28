"""
Transformador de lecturas de sensores.

ETL — Fase TRANSFORM:
Convierte documentos crudos de MongoDB (una lectura cada 15 min)
en un DataFrame con una fila por localidad × día, con promedios y extremos.

Reglas de limpieza aplicadas:
  - HUMEDAD_SUELO: valores válidos entre 10% y 100%
  - TEMPERATURA:   valores válidos entre -10°C y 50°C
  - Registros fuera de rango se descartan y se loguean
  - Nulls resultantes se dejan como None (no se imputan con 0)
"""
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Rangos válidos por tipo de lectura
RANGOS_VALIDOS = {
    "HUMEDAD_SUELO": (10.0, 100.0),
    "TEMPERATURA":   (-10.0, 50.0),
}


def transform_readings(
    raw_data: list[dict],
    lote_localidad_map: dict[int, int] | None = None,
) -> pd.DataFrame:
    """
    Limpia y agrega lecturas crudas de sensores.

    Proceso:
        1. Normaliza timestamps a fecha (día).
        2. Filtra outliers POR TIPO de lectura (no un filtro único para todos).
        3. Mapea lote_id → localidad_id usando lote_localidad_map.
        4. Agrega: promedio, max y min diario por localidad × tipo_lectura.
        5. Pivotea al formato tabular esperado por el loader.

    Args:
        raw_data: Lista de dicts con campos lote_id, timestamp,
                  tipo_lectura, valor.
        lote_localidad_map: Dict {lote_id: localidad_id}. Si es None,
                  se usa lote_id directamente como localidad_id (fallback).

    Returns:
        DataFrame con columnas: localidad_id, fecha, temp_promedio,
        temp_max, temp_min, humedad_promedio.
        Los nulls se dejan como NaN — no se imputan con 0.
    """
    if not raw_data:
        logger.warning("Sin datos crudos para transformar.")
        return pd.DataFrame()

    df = pd.DataFrame(raw_data)
    logger.info(f"Transformando {len(df)} lecturas crudas...")

    # 1. Normalizar timestamps
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["fecha"] = df["timestamp"].dt.date

    # 2. Filtrar outliers POR tipo de lectura
    filas_antes = len(df)
    masks = []
    for tipo, (minv, maxv) in RANGOS_VALIDOS.items():
        mask = (df["tipo_lectura"] == tipo) & df["valor"].between(minv, maxv)
        masks.append(mask)
        descartados = ((df["tipo_lectura"] == tipo) & ~df["valor"].between(minv, maxv)).sum()
        if descartados > 0:
            logger.warning(f"Outliers descartados en {tipo}: {descartados} registros.")

    tipos_conocidos = set(RANGOS_VALIDOS.keys())
    mask_otros = ~df["tipo_lectura"].isin(tipos_conocidos)
    df = df[pd.concat(masks + [mask_otros.to_frame()], axis=1).any(axis=1)]

    logger.info(f"Outliers eliminados: {filas_antes - len(df)} registros.")

    # Guard: si todos los datos fueron filtrados, retornar DF vacío
    if df.empty:
        logger.warning("Sin datos válidos tras el filtrado de outliers. Retornando DF vacío.")
        return pd.DataFrame()

    # 3. Mapear lote_id → localidad_id
    if lote_localidad_map:
        df["localidad_id"] = df["lote_id"].map(lote_localidad_map)
        sin_mapeo = df["localidad_id"].isna().sum()
        if sin_mapeo > 0:
            logger.warning(f"{sin_mapeo} lecturas sin mapeo lote→localidad; se descartan.")
        df = df.dropna(subset=["localidad_id"])
        df["localidad_id"] = df["localidad_id"].astype(int)
    else:
        df["localidad_id"] = df["lote_id"]

    # 4. Agregación diaria por localidad × tipo_lectura
    agg = df.groupby(["localidad_id", "fecha", "tipo_lectura"])["valor"].agg(
        promedio="mean",
        maximo="max",
        minimo="min"
    ).reset_index()

    # 5. Pivot — una columna por métrica
    pivot_prom = agg.pivot(
        index=["localidad_id", "fecha"],
        columns="tipo_lectura",
        values="promedio"
    ).reset_index()

    temp_agg = agg[agg["tipo_lectura"] == "TEMPERATURA"].copy()
    pivot_temp = temp_agg.pivot(
        index=["localidad_id", "fecha"],
        columns="tipo_lectura",
        values=["maximo", "minimo"]
    )
    pivot_temp.columns = ["temp_max", "temp_min"]
    pivot_temp = pivot_temp.reset_index(drop=True)

    resultado = pd.concat([pivot_prom, pivot_temp], axis=1)

    resultado = resultado.rename(columns={
        "HUMEDAD_SUELO": "humedad_promedio",
        "TEMPERATURA":   "temp_promedio",
    })

    logger.info(f"Transformación completa: {len(resultado)} filas resultantes.")
    return resultado
