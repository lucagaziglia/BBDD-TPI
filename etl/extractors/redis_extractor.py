"""
Extractor de Redis.
Se conecta a Redis Cloud para recuperar el último estado de los sensores
y maquinarias.
"""
import os
import logging
import redis

logger = logging.getLogger(__name__)

def extract_realtime_state() -> dict:
    """
    Extrae el estado en tiempo real desde Redis Cloud.
    Ideal para alimentar un panel rápido sin latencia.
    """
    url = os.getenv("REDIS_URL")
    if not url:
        logger.warning("REDIS_URL no está configurada. Retornando datos mockeados.")
        return {"sensor:1:HUMEDAD_SUELO": "25.5", "sensor:1:ts": "2025-01-20T10:00:00Z"}
    
    try:
        r = redis.Redis.from_url(url, decode_responses=True)
        keys = r.keys("sensor:*")
        state = {}
        for key in keys:
            state[key] = r.get(key)
            
        logger.info(f"Se extrajeron {len(keys)} keys de estado desde Redis.")
        return state
    except Exception as e:
        logger.error(f"Error extrayendo de Redis: {e}")
        return {}
