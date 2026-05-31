"""
cassandra_extractor.py — Extractor unificado de la capa NoSQL.

Reemplaza a `mongodb_extractor` (histórico) y `redis_extractor` (estado real-time).
Ahora ambos viven en Astra DB (Cassandra), en tablas separadas del mismo keyspace.

Usa AstrayPy (Data API REST) — no requiere Secure Connect Bundle, solo token + URL.

Tres responsabilidades:

  1) `connect_astradb()`      → factory que devuelve colección Astra DB (AstrayPy).

  2) `extract_sensor_readings(desde, hasta)` → reemplaza al extractor Mongo.
                                  Devuelve la misma lista de dicts que antes
                                  para no romper el transformer.

  3) `extract_realtime_state()` → reemplaza al extractor Redis. Devuelve un
                                  dict con el mismo formato `sensor:{id}:tipo`
                                  para no romper consumidores existentes.

Si no hay conexión disponible (sin Astra configurado o si la conexión falla),
las dos funciones de extracción caen a datos mock para permitir correr el
pipeline sin depender de infraestructura externa.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────────
# Conexión a Astra DB vía AstrayPy (Data API REST)
# ────────────────────────────────────────────────────────────────────────────

def connect_astradb(collection_name: str = "sensor_readings"):
    """
    Conecta a Astra DB usando AstrayPy (Data API REST).
    """
    from astrapy import DataAPIClient

    
    url = os.getenv("ASTRA_DB_URL")
    token = os.getenv("ASTRA_DB_TOKEN")
    keyspace = os.getenv("CASSANDRA_KEYSPACE", "default_keyspace")
    
    if not (url and token):
        logger.warning(
            "ASTRA_DB_URL o ASTRA_DB_TOKEN no configurados en .env. "
        )
        return None
    
    try:
        client = DataAPIClient(token=token)
        db = client.get_database(url, keyspace=keyspace)
        collection = db.get_collection(collection_name)
        logger.info(f"Conectado a Astra DB (colección={collection_name}).")
        return collection
    except Exception as e:
        logger.warning(f"Astra DB no disponible ({type(e).__name__}: {e}).")
        return None


# ────────────────────────────────────────────────────────────────────────────
# Mock data — fallback cuando no hay infra disponible
# ────────────────────────────────────────────────────────────────────────────

_LOTE_TIPO_SUELO = {
     1: "Franco limoso",     2: "Franco arcilloso",  3: "Arenoso",
     4: "Franco limoso",     5: "Arcilloso",
     6: "Franco limoso",     7: "Franco arcilloso",  8: "Arcilloso",
     9: "Vertisol",         10: "Vertisol",          11: "Arenoso",
    12: "Franco limoso",    13: "Franco limoso",     14: "Franco arcilloso",
    15: "Arcilloso",        16: "Franco limoso",     17: "Arenoso",
    18: "Franco limoso",    19: "Arcilloso",
    20: "Franco limoso",    21: "Arcilloso",
    22: "Franco limoso",    23: "Vertisol",
    24: "Franco arcilloso", 25: "Franco limoso",
}

_HUMEDAD_BASE = {
    "Franco":           68.0,
    "Franco limoso":    66.0,
    "Franco arcilloso": 64.0,
    "Arcilloso":        62.0,
    "Arenoso":          54.0,
    "Vertisol":         70.0,
}


def _generate_mock_readings(n_dias: int = 7) -> list[dict]:
    """
    Lecturas sintéticas con la misma estructura que devuelve la query a
    `sensor_readings` en Cassandra. Útil para tests y demo offline.

    Las fechas se anclan a "ahora" (en lugar de una fecha fija) para que el
    pipeline real, que filtra por `datetime.now() - N días`, siempre encuentre
    datos en el rango pedido. Si las anclamos a una fecha fija (p. ej.
    2025-06-28) y corremos el ETL meses después, el filtro deja todo afuera.
    """
    import random
    docs = []
    ahora  = datetime.now().replace(minute=0, second=0, microsecond=0)
    inicio = ahora - timedelta(days=n_dias)

    for lote_id, tipo_suelo in _LOTE_TIPO_SUELO.items():
        humedad_base = _HUMEDAD_BASE.get(tipo_suelo, 62.0)
        ts = inicio
        while ts <= ahora:
            hora = ts.hour
            var_temp = 8.0 * abs(hora - 14) / 14 * (-1 if hora < 14 else 1)
            docs.append({
                "lote_id":       lote_id,
                "timestamp":     ts,
                "temp":          round(18.0 + var_temp + random.gauss(0, 1.2), 2),
                "humedad_suelo": round(humedad_base + random.gauss(0, 3.5), 2),
                "precipitacion": round(random.uniform(0, 5) if random.random() > 0.8 else 0.0, 2),
                "agua":          round(random.uniform(10, 50), 2),
            })
            ts += timedelta(hours=1)
    return docs


MOCK_READINGS: list[dict] = _generate_mock_readings(n_dias=30)

MOCK_STATE: dict[str, str] = {
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


# ────────────────────────────────────────────────────────────────────────────
# Extractores
# ────────────────────────────────────────────────────────────────────────────

def extract_sensor_readings(desde: datetime, hasta: datetime) -> list[dict]:
    """
    Extrae las lecturas crudas de sensor_readings entre desde y hasta

    estructura:
        [{"lote_id": int, "timestamp": dt, "temp": float,
          "humedad_suelo": float, "precipitacion": float, "agua": float}, …]
    """
    collection = connect_astradb("sensor_readings")
    
    if collection is None:
        logger.warning("Astra DB no disponible — usando datos mock para testing.")
        return _filter_by_date(MOCK_READINGS, desde, hasta)
    
    try:
        logger.info(f"Extrayendo de Astra DB: {desde} → {hasta}")
        
        # timestamps a ISO 8601 string sin microsegundos + Z
        desde_iso = desde.replace(microsecond=0).isoformat() + "Z"
        hasta_iso = hasta.replace(microsecond=0).isoformat() + "Z"
        
        # Query con filtro de rango de timestamps (como strings ISO)
        results = collection.find({
            "timestamp": {
                "$gte": desde_iso,
                "$lte": hasta_iso
            }
        })
        
        readings = []
        for doc in results:
            # Rquitamos id de la base
            if "_id" in doc:
                doc.pop("_id")
            # Convertir timestamp string back to datetime si es necesario
            if isinstance(doc.get("timestamp"), str):
                doc["timestamp"] = datetime.fromisoformat(doc["timestamp"].replace("Z", "+00:00"))
            readings.append(doc)
        
        logger.info(f"Extraídas {len(readings)} filas desde Astra DB.")
        return readings
    
    except Exception as e:
        logger.warning(f"Error extrayendo de Astra DB ({type(e).__name__}: {e}). Cayendo a mock.")
        return _filter_by_date(MOCK_READINGS, desde, hasta)


def extract_realtime_state() -> dict[str, str]:
    """
    Extrae sensor_realtime y riego_estado.

    Para preservar la API del consumidor anterior (que recibía un dict con
    claves estilo `sensor:{id}:humedad`), aplastamos las dos colecciones en ese mismo formato
    """
    collection = connect_astradb("sensor_realtime")
    
    if collection is None:
        logger.warning("Astra DB no disponible — usando datos mock para testing.")
        return dict(MOCK_STATE)
    
    try:
        state: dict[str, str] = {}
        
        # datos de sensor_realtime
        try:
            realtime_docs = collection.find({})
            for doc in realtime_docs:
                lote_id = doc.get("lote_id")
                humedad = doc.get("humedad")
                temperatura = doc.get("temperatura")
                
                if lote_id and humedad is not None:
                    state[f"sensor:{lote_id}:humedad"] = str(humedad)
                if lote_id and temperatura is not None:
                    state[f"sensor:{lote_id}:temperatura"] = str(temperatura)
        except Exception as e:
            logger.warning(f"Error extrayendo sensor_realtime: {e}")
        
        # Datos de riego_estado
        try:
            riego_collection = connect_astradb("riego_estado")
            if riego_collection:
                riego_docs = riego_collection.find({})
                for doc in riego_docs:
                    lote_id = doc.get("lote_id")
                    estado = doc.get("estado")
                    if lote_id and estado:
                        state[f"riego:{lote_id}:estado"] = estado
        except Exception as e:
            logger.warning(f"Error extrayendo riego_estado: {e}")
        
        logger.info(f"Extraídas {len(state)} entradas de estado real-time.")
        return state
    
    except Exception as e:
        logger.error(f"Error extrayendo estado real-time: {e}")
        return {}


#Helpers

def _filter_by_date(docs: list[dict], desde: datetime, hasta: datetime) -> list[dict]:
    """Filtra los mock readings por rango de fechas para imitar la slice query."""
    return [d for d in docs if desde <= d["timestamp"] <= hasta]
