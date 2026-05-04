import pandas as pd
import logging
from datetime import date

logger = logging.getLogger(__name__)

RANGOS_VALIDOS = {
    "HUMEDAD_SUELO": (10.0, 100.0),
    "TEMPERATURA":   (-10.0, 50.0),
}


def transform_readings(
    raw_data: list[dict],
    tiempo_map: dict[date, int] | None = None,
    lotes_activos: set[int] | None = None,
) -> pd.DataFrame:
    if not raw_data:
        logger.warning("Sin datos crudos para transformar.")
        return pd.DataFrame()

    df = pd.DataFrame(raw_data)
    logger.info(f"Transformando {len(df)} lecturas crudas...")

    df["timestamp"]  = pd.to_datetime(df["timestamp"])
    df["mes_inicio"] = df["timestamp"].dt.to_period("M").dt.start_time.dt.date

    filas_antes = len(df)
    masks = []
    for tipo, (minv, maxv) in RANGOS_VALIDOS.items():
        mask = (df["tipo_lectura"] == tipo) & df["valor"].between(minv, maxv)
        masks.append(mask)
        descartados = (
            (df["tipo_lectura"] == tipo) & ~df["valor"].between(minv, maxv)
        ).sum()
        if descartados > 0:
            logger.warning(f"Outliers descartados en {tipo}: {descartados} registros.")

    tipos_conocidos = set(RANGOS_VALIDOS.keys())
    mask_otros = ~df["tipo_lectura"].isin(tipos_conocidos)
    df = df[pd.concat(masks + [mask_otros.to_frame()], axis=1).any(axis=1)]
    logger.info(f"Outliers eliminados: {filas_antes - len(df)} registros.")

    if df.empty:
        logger.warning("Sin datos válidos tras el filtrado de outliers.")
        return pd.DataFrame()

    if lotes_activos:
        antes = len(df)
        df = df[df["lote_id"].isin(lotes_activos)]
        descartados = antes - len(df)
        if descartados > 0:
            logger.warning(f"{descartados} lecturas de lotes inactivos/inexistentes descartadas.")
        if df.empty:
            logger.warning("Sin lecturas en lotes activos. Retornando DF vacío.")
            return pd.DataFrame()

    if not tiempo_map:
        logger.error(
            "tiempo_map vacío: no se puede resolver tiempo_id. "
            "Verificar que dim_tiempo esté seedeada y las credenciales Supabase configuradas."
        )
        return pd.DataFrame()

    df["tiempo_id"] = df["mes_inicio"].map(tiempo_map)
    sin_mapeo = df["tiempo_id"].isna().sum()
    if sin_mapeo > 0:
        meses_sin_mapeo = sorted(df.loc[df["tiempo_id"].isna(), "mes_inicio"].unique())
        logger.warning(
            f"{sin_mapeo} lecturas sin mapeo fecha→tiempo_id; meses ausentes en dim_tiempo: "
            f"{[str(m) for m in meses_sin_mapeo]}"
        )
    df = df.dropna(subset=["tiempo_id"])
    if df.empty:
        logger.warning("Ninguna lectura pudo mapearse a tiempo_id.")
        return pd.DataFrame()
    df["tiempo_id"] = df["tiempo_id"].astype(int)
    df["lote_id"]   = df["lote_id"].astype(int)

    agg = df.groupby(["lote_id", "tiempo_id", "tipo_lectura"])["valor"].agg(
        promedio="mean",
        maximo="max",
        minimo="min",
    ).reset_index()

    pivot_prom = agg.pivot(
        index=["lote_id", "tiempo_id"],
        columns="tipo_lectura",
        values="promedio",
    ).reset_index()
    pivot_prom.columns.name = None
    pivot_prom = pivot_prom.rename(columns={
        "HUMEDAD_SUELO": "humedad_promedio",
        "TEMPERATURA":   "temp_promedio",
    })

    temp_agg = agg[agg["tipo_lectura"] == "TEMPERATURA"][
        ["lote_id", "tiempo_id", "maximo", "minimo"]
    ].rename(columns={"maximo": "temp_max", "minimo": "temp_min"})

    resultado = pivot_prom.merge(
        temp_agg, on=["lote_id", "tiempo_id"], how="left"
    )

    if "humedad_promedio" in resultado.columns:
        resultado["precipitacion_mm"] = (
            (resultado["humedad_promedio"] - 50).clip(lower=0) * 0.5
        ).round(2)
    else:
        resultado["precipitacion_mm"] = None

    columnas_esperadas = [
        "lote_id", "tiempo_id",
        "temp_promedio", "temp_max", "temp_min",
        "humedad_promedio", "precipitacion_mm",
    ]
    for col in columnas_esperadas:
        if col not in resultado.columns:
            resultado[col] = None
    resultado = resultado[columnas_esperadas]

    logger.info(f"Transformación completa: {len(resultado)} filas (lote × tiempo).")
    return resultado
