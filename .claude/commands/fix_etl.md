# /fix_etl — Corregir y completar el pipeline ETL

Corregí los 5 archivos del pipeline ETL según los problemas identificados.
No preguntes nada, aplicá todos los fixes directamente.

---

## Archivo 1 — `etl/extractors/mongodb_extractor.py`

Reemplazá el contenido completo con esto:

```python
"""
Extractor de MongoDB Atlas.

ETL — Fase EXTRACT:
Lee documentos crudos de la colección `sensor_readings` para un rango de fechas.
No transforma ni filtra nada: retorna los documentos tal cual vienen de MongoDB.
Los datos crudos son lecturas de sensores cada 15 minutos por lote.
"""
import os
import logging
from pymongo import MongoClient
from datetime import datetime

logger = logging.getLogger(__name__)

# Datos mock realistas para correr sin credenciales reales
MOCK_READINGS = [
    {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8,  0), "tipo_lectura": "HUMEDAD_SUELO", "valor": 62.3},
    {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 15), "tipo_lectura": "HUMEDAD_SUELO", "valor": 61.8},
    {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8,  0), "tipo_lectura": "TEMPERATURA",   "valor": 21.4},
    {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 15), "tipo_lectura": "TEMPERATURA",   "valor": 21.6},
    {"lote_id": 2, "timestamp": datetime(2024, 11, 3, 8,  0), "tipo_lectura": "HUMEDAD_SUELO", "valor": 45.1},
    {"lote_id": 2, "timestamp": datetime(2024, 11, 3, 8, 15), "tipo_lectura": "HUMEDAD_SUELO", "valor": 44.8},
    {"lote_id": 2, "timestamp": datetime(2024, 11, 3, 8,  0), "tipo_lectura": "TEMPERATURA",   "valor": 23.0},
    {"lote_id": 2, "timestamp": datetime(2024, 11, 3, 8, 15), "tipo_lectura": "TEMPERATURA",   "valor": 22.7},
    {"lote_id": 3, "timestamp": datetime(2024, 11, 3, 8,  0), "tipo_lectura": "HUMEDAD_SUELO", "valor": 71.5},
    {"lote_id": 3, "timestamp": datetime(2024, 11, 3, 8,  0), "tipo_lectura": "TEMPERATURA",   "valor": 19.8},
]


def extract_sensor_readings(desde: datetime, hasta: datetime) -> list[dict]:
    """
    Extrae lecturas de sensores de MongoDB Atlas entre las fechas dadas.

    Args:
        desde: Fecha/hora de inicio del período a extraer.
        hasta: Fecha/hora de fin del período a extraer.

    Returns:
        Lista de documentos crudos sin transformar. Cada documento tiene:
        lote_id, timestamp, tipo_lectura (HUMEDAD_SUELO | TEMPERATURA), valor.
    """
    uri = os.getenv("MONGODB_URI")
    if not uri:
        logger.warning("MONGODB_URI no configurada — usando datos mock para testing.")
        return MOCK_READINGS

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Nombre explícito de la base — nunca usar get_database() sin argumento
        db = client["agtech_sensors"]
        collection = db["sensor_readings"]

        query = {"timestamp": {"$gte": desde, "$lte": hasta}}
        logger.info(f"Extrayendo de MongoDB: {desde} → {hasta}")
        readings = list(collection.find(query))
        logger.info(f"Extraídos {len(readings)} documentos.")
        client.close()
        return readings

    except Exception as e:
        logger.error(f"Error extrayendo de MongoDB: {e}")
        return []
```

---

## Archivo 2 — `etl/extractors/redis_extractor.py`

Reemplazá el contenido completo con esto:

```python
"""
Extractor de Redis Cloud.

ETL — Fase EXTRACT (tiempo real):
Lee el ÚLTIMO valor conocido de cada sensor desde Redis.
Redis almacena solo el estado actual — no el historial.
Se usa para dashboards en tiempo real y decisiones de riego inmediatas.

Estructura de keys en Redis:
  sensor:{lote_id}:humedad      → float, ej: "62.3"
  sensor:{lote_id}:temperatura  → float, ej: "21.4"
  riego:{lote_id}:estado        → string, "ON" | "OFF"
"""
import os
import logging
import redis

logger = logging.getLogger(__name__)

MOCK_STATE = {
    "sensor:1:humedad":     "62.3",
    "sensor:1:temperatura": "21.4",
    "sensor:2:humedad":     "45.1",
    "sensor:2:temperatura": "23.0",
    "sensor:3:humedad":     "71.5",
    "sensor:3:temperatura": "19.8",
    "riego:1:estado":       "ON",
    "riego:2:estado":       "OFF",
    "riego:3:estado":       "OFF",
}


def extract_realtime_state() -> dict:
    """
    Extrae el estado en tiempo real de todos los sensores desde Redis.

    Returns:
        Dict con todas las keys sensor:* y riego:* y sus valores actuales.
        Ejemplo: {"sensor:1:humedad": "62.3", "riego:1:estado": "ON", ...}
    """
    url = os.getenv("REDIS_URL")
    if not url:
        logger.warning("REDIS_URL no configurada — usando datos mock para testing.")
        return MOCK_STATE

    try:
        r = redis.Redis.from_url(url, decode_responses=True)

        # IMPORTANTE: usar scan_iter en lugar de keys()
        # r.keys() es O(N) y bloquea Redis mientras escanea todo el keyspace.
        # scan_iter() itera en lotes sin bloquear — correcto para producción.
        state = {}
        for key in r.scan_iter("sensor:*"):
            state[key] = r.get(key)
        for key in r.scan_iter("riego:*"):
            state[key] = r.get(key)

        logger.info(f"Extraídas {len(state)} keys de Redis.")
        return state

    except Exception as e:
        logger.error(f"Error extrayendo de Redis: {e}")
        return {}
```

---

## Archivo 3 — `etl/transformers/sensor_transformer.py`

Reemplazá el contenido completo con esto:

```python
"""
Transformador de lecturas de sensores.

ETL — Fase TRANSFORM:
Convierte documentos crudos de MongoDB (una lectura cada 15 min)
en un DataFrame con una fila por lote × día, con promedios y extremos.

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


def transform_readings(raw_data: list[dict]) -> pd.DataFrame:
    """
    Limpia y agrega lecturas crudas de sensores.

    Proceso:
        1. Normaliza timestamps a fecha (día).
        2. Filtra outliers POR TIPO de lectura (no un filtro único para todos).
        3. Agrega: promedio, max y min diario por lote × tipo_lectura.
        4. Pivotea al formato tabular esperado por el loader.

    Args:
        raw_data: Lista de dicts con campos lote_id, timestamp,
                  tipo_lectura, valor.

    Returns:
        DataFrame con columnas: lote_id, fecha, HUMEDAD_SUELO,
        TEMPERATURA, TEMPERATURA_max, TEMPERATURA_min.
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

    # También pasar lecturas de tipos no definidos en RANGOS_VALIDOS sin filtrar
    tipos_conocidos = set(RANGOS_VALIDOS.keys())
    mask_otros = ~df["tipo_lectura"].isin(tipos_conocidos)
    df = df[pd.concat(masks + [mask_otros.to_frame()], axis=1).any(axis=1)]

    logger.info(f"Outliers eliminados: {filas_antes - len(df)} registros.")

    # 3. Agregación diaria por lote × tipo_lectura
    agg = df.groupby(["lote_id", "fecha", "tipo_lectura"])["valor"].agg(
        promedio="mean",
        maximo="max",
        minimo="min"
    ).reset_index()

    # 4. Pivot — una columna por métrica
    # Promedios
    pivot_prom = agg.pivot(
        index=["lote_id", "fecha"],
        columns="tipo_lectura",
        values="promedio"
    ).reset_index()

    # Máx y mín solo para temperatura (para dim_clima)
    temp_agg = agg[agg["tipo_lectura"] == "TEMPERATURA"].copy()
    pivot_temp = temp_agg.pivot(
        index=["lote_id", "fecha"],
        columns="tipo_lectura",
        values=["maximo", "minimo"]
    )
    pivot_temp.columns = ["temp_max", "temp_min"]
    pivot_temp = pivot_temp.reset_index(drop=True)

    resultado = pd.concat([pivot_prom, pivot_temp], axis=1)

    # Renombrar columnas al formato de dim_clima
    resultado = resultado.rename(columns={
        "HUMEDAD_SUELO": "humedad_promedio",
        "TEMPERATURA":   "temp_promedio",
    })

    # IMPORTANTE: no imputar nulls con 0 — dejar NaN para que el loader
    # inserte NULL en la BD, que es semánticamente distinto de "valor 0".
    logger.info(f"Transformación completa: {len(resultado)} filas resultantes.")
    return resultado
```

---

## Archivo 4 — `etl/loaders/supabase_loader.py`

Reemplazá el contenido completo con esto:

```python
"""
Loader para Supabase (PostgreSQL).

ETL — Fase LOAD:
Inserta o actualiza los datos transformados en la tabla dim_clima
del Datawarehouse usando UPSERT (INSERT ... ON CONFLICT DO UPDATE).

El UPSERT garantiza idempotencia: correr el pipeline dos veces
sobre el mismo período no duplica datos.
"""
import os
import logging
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)


def load_to_dim_clima(df: pd.DataFrame) -> int:
    """
    Carga el DataFrame transformado en la tabla dim_clima de Supabase.

    Usa UPSERT: si ya existe una fila para (lote_id, fecha), la actualiza.
    Si no existe, la inserta. Esto hace el pipeline idempotente.

    Args:
        df: DataFrame con columnas lote_id, fecha, temp_promedio,
            temp_max, temp_min, humedad_promedio.

    Returns:
        Cantidad de filas insertadas o actualizadas.
    """
    if df.empty:
        logger.info("DataFrame vacío, nada para cargar.")
        return 0

    db_url = os.getenv("SUPABASE_DB_URL")
    if not db_url:
        logger.warning("SUPABASE_DB_URL no configurada — simulando carga (modo dry-run).")
        logger.info(f"[DRY-RUN] Se cargarían {len(df)} filas a dim_clima.")
        return len(df)

    upsert_query = """
        INSERT INTO dim_clima
            (lote_id, fecha, temp_promedio, temp_max, temp_min, humedad_promedio)
        VALUES %s
        ON CONFLICT (lote_id, fecha) DO UPDATE SET
            temp_promedio    = EXCLUDED.temp_promedio,
            temp_max         = EXCLUDED.temp_max,
            temp_min         = EXCLUDED.temp_min,
            humedad_promedio = EXCLUDED.humedad_promedio,
            created_at       = NOW()
    """

    # Columnas esperadas — None si no existe la columna en el df
    def safe(row, col):
        return float(row[col]) if col in df.columns and pd.notna(row.get(col)) else None

    tuples = [
        (
            int(row["lote_id"]),
            row["fecha"],
            safe(row, "temp_promedio"),
            safe(row, "temp_max"),
            safe(row, "temp_min"),
            safe(row, "humedad_promedio"),
        )
        for _, row in df.iterrows()
    ]

    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        execute_values(cursor, upsert_query, tuples)
        conn.commit()
        filas = cursor.rowcount
        cursor.close()
        conn.close()
        logger.info(f"Carga completada: {filas} filas en dim_clima.")
        return filas

    except Exception as e:
        logger.error(f"Error cargando en Supabase: {e}")
        return 0


# Mantener compatibilidad con el nombre anterior usado en pipeline.py
load_to_staging = load_to_dim_clima
```

---

## Archivo 5 — `etl/pipeline.py`

Reemplazá el contenido completo con esto:

```python
"""
Pipeline ETL principal — AgTech Datawarehouse

ETL completo: MongoDB + Redis → transformación → Supabase.

Uso desde la raíz del repo:
    python etl/pipeline.py

Uso desde dentro de etl/:
    python pipeline.py
"""
import sys
import os
import logging
from datetime import datetime, timedelta

# Fix de path: permite correr el script desde la raíz del repo
# sin que Python pierda los imports relativos dentro de etl/
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from extractors.mongodb_extractor import extract_sensor_readings
from extractors.redis_extractor import extract_realtime_state
from transformers.sensor_transformer import transform_readings
from loaders.supabase_loader import load_to_staging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()


def run_pipeline(dias: int = 30) -> dict:
    """
    Ejecuta el pipeline ETL completo.

    Args:
        dias: Cantidad de días hacia atrás a procesar. Default: 30.

    Returns:
        Dict con resultados: filas_extraidas, filas_transformadas, filas_cargadas.
    """
    resultados = {"filas_extraidas": 0, "filas_transformadas": 0, "filas_cargadas": 0}
    inicio = datetime.now()
    logger.info(f"=== Iniciando pipeline ETL (últimos {dias} días) ===")

    # ── PASO 1: EXTRACT ──────────────────────────────────────────────
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

    # ── PASO 2: TRANSFORM ────────────────────────────────────────────
    logger.info("PASO 2/3 — Transform")
    df_transformado = transform_readings(raw_mongo)
    resultados["filas_transformadas"] = len(df_transformado)

    if df_transformado.empty:
        logger.warning("Transform produjo DataFrame vacío. Abortando carga.")
        return resultados

    # ── PASO 3: LOAD ─────────────────────────────────────────────────
    logger.info("PASO 3/3 — Load")
    filas_cargadas = load_to_staging(df_transformado)
    resultados["filas_cargadas"] = filas_cargadas

    # ── RESUMEN ──────────────────────────────────────────────────────
    duracion = (datetime.now() - inicio).total_seconds()
    logger.info(f"=== Pipeline completado en {duracion:.1f}s ===")
    logger.info(f"    Extraídos:    {resultados['filas_extraidas']} documentos MongoDB")
    logger.info(f"    Transformados:{resultados['filas_transformadas']} filas")
    logger.info(f"    Cargados:     {resultados['filas_cargadas']} filas en dim_clima")
    return resultados


if __name__ == "__main__":
    run_pipeline()
```

---

## Verificación final

Después de aplicar todos los cambios, corré esto desde la raíz del repo:

```bash
python etl/pipeline.py
```

Debería ver en la terminal:
```
PASO 1/3 — Extract
MongoDB: 10 documentos | Redis: 9 keys
PASO 2/3 — Transform
Transformación completa: 3 filas resultantes.
PASO 3/3 — Load
[DRY-RUN] Se cargarían 3 filas a dim_clima.
Pipeline completado en 0.1s
```

Si funciona en dry-run, el pipeline está listo para conectar con las credenciales reales en `.env`.
