"""
Seed de Redis Cloud — estado en tiempo real

Setea el último estado conocido de cada sensor y el estado
del sistema de riego para todos los lotes.

Uso:
    python nosql/redis/seed_realtime.py

Requiere en .env:
    REDIS_URL=redis://default:pass@host:port
"""
import os
import sys
import random
import logging
import redis
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Mismo set de lotes que MongoDB
LOTES = [
    (1,  "Lote 1 - La Esperanza",  "franco",            67.0),
    (2,  "Lote 2 - La Esperanza",  "franco-arcilloso",  64.0),
    (3,  "Lote 3 - La Esperanza",  "arcilloso",         62.0),
    (4,  "Lote 1 - Norte Junín",   "franco",            67.0),
    (5,  "Lote 2 - Norte Junín",   "franco-limoso",     66.0),
    (6,  "Lote 1 - Tres Marías",   "franco",            67.0),
    (7,  "Lote 2 - Tres Marías",   "arcilloso",         62.0),
    (8,  "Lote 3 - Tres Marías",   "franco-arcilloso",  64.0),
    (9,  "Lote 1 - La Rinconada",  "franco",            67.0),
    (10, "Lote 2 - La Rinconada",  "franco-limoso",     66.0),
    (11, "Lote 3 - La Rinconada",  "arenoso",           54.0),
    (12, "Lote 1 - Del Paraná",    "franco",            67.0),
    (13, "Lote 2 - Del Paraná",    "arcilloso",         62.0),
]

# Umbral: si humedad < 45% activa riego automáticamente
UMBRAL_RIEGO = 45.0


def run_seed():
    url = os.getenv("REDIS_URL")
    if not url:
        logger.error("REDIS_URL no configurada en .env. Abortando.")
        sys.exit(1)

    r = redis.Redis.from_url(url, decode_responses=True)

    # Verificar conexión
    r.ping()
    logger.info("Conexión a Redis Cloud exitosa.")

    total_keys = 0
    for lote_id, nombre, tipo_suelo, humedad_base in LOTES:
        humedad  = round(humedad_base + random.gauss(0, 4.0), 2)
        temp     = round(18.0 + random.gauss(0, 2.5), 2)
        # Riego ON si humedad baja del umbral
        estado_riego = "ON" if humedad < UMBRAL_RIEGO else "OFF"

        # SET con expiración de 1 hora (los sensores actualizan c/15min)
        ttl = 3600
        r.set(f"sensor:{lote_id}:humedad",     humedad,  ex=ttl)
        r.set(f"sensor:{lote_id}:temperatura", temp,     ex=ttl)
        r.set(f"riego:{lote_id}:estado",       estado_riego, ex=ttl)

        total_keys += 3
        estado_str = "RIEGO ON" if estado_riego == "ON" else "riego off"
        logger.info(f"  {nombre}: humedad={humedad}% temp={temp}°C → {estado_str}")

    logger.info(f"Seed Redis completado: {total_keys} keys seteadas.")
    logger.info("Estructura: sensor:{id}:humedad | sensor:{id}:temperatura | riego:{id}:estado")


if __name__ == "__main__":
    run_seed()
