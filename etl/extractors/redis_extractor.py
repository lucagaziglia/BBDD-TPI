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
