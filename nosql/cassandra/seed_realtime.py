"""
Carga del "estado actual" de los sensores en Astra DB (colecciones sensor_realtime
y riego_estado).

Estructura de documentos:

sensor_realtime:
    {
        "lote_id": int,
        "humedad": float,
        "temperatura": float,
        "updated_at": string (ISO 8601)
    }

riego_estado:
    {
        "lote_id": int,
        "estado": "ON" | "OFF",
        "motivo": string,
        "updated_at": string (ISO 8601)
    }

Correr con:
    python nosql/cassandra/seed_realtime.py
"""
import os
import sys
import random
import logging
from datetime import datetime

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from etl.extractors.cassandra_extractor import connect_astradb  # noqa: E402

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


HUMEDAD_BASE = {
    "Franco limoso":    66.0,
    "Franco arcilloso": 64.0,
    "Arcilloso":        62.0,
    "Arenoso":          54.0,
    "Vertisol":         70.0,
}

LOTES = [
    (1,  "Lote C",                "Arcilloso"),
    (2,  "Lote B",                "Franco arcilloso"),
    (3,  "Lote A",                "Franco limoso"),
    (4,  "Lote 3 - La Rinconada", "Arenoso"),
    (5,  "Lote 2 - Laguna",       "Franco arcilloso"),
    (6,  "Lote 1 - Arroyo",       "Franco limoso"),
    (7,  "Lote 2 - Sur",          "Arcilloso"),
    (8,  "Lote 1 - Norte",        "Franco limoso"),
    (9,  "Lote 4 (San Cayetano)", "Arcilloso"),
    (10, "Lote 3 (San Cayetano)", "Franco limoso"),
    (11, "Lote 2 (San Cayetano)", "Arenoso"),
    (12, "Lote 1 (San Cayetano)", "Franco limoso"),
    (13, "Lote 4 (Barrancosa)",   "Franco limoso"),
    (14, "Lote 3 (Barrancosa)",   "Arenoso"),
    (15, "Lote 2 (Barrancosa)",   "Vertisol"),
    (16, "Lote 1 (Barrancosa)",   "Vertisol"),
    (17, "Lote 2 - Secundario",   "Franco limoso"),
    (18, "Lote 1 - Principal",    "Franco arcilloso"),
    (19, "Lote 3 - Centro",       "Arcilloso"),
    (20, "Lote 2 - Oeste",        "Franco arcilloso"),
    (21, "Lote 1 - Este",         "Franco limoso"),
    (22, "Lote Sur",              "Arcilloso"),
    (23, "Lote Norte",            "Franco limoso"),
    (24, "Lote 2 (El Retiro)",    "Vertisol"),
    (25, "Lote 1 (El Retiro)",    "Franco limoso"),
]

UMBRAL_RIEGO = 45.0


def run_seed() -> tuple[int, int]:
    realtime_coll = connect_astradb("sensor_realtime")
    riego_coll = connect_astradb("riego_estado")
    
    if realtime_coll is None or riego_coll is None:
        logger.error("No se pudo conectar a Astra DB. Verificá las variables de entorno.")
        sys.exit(1)

    # Limpiamos las colecciones
    logger.info("Limpiando colecciones…")
    realtime_coll.delete_many({})
    riego_coll.delete_many({})

    ahora = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    total_docs = 0
    riegos_on = 0

    for lote_id, _nombre, tipo_suelo in LOTES:
        humedad_base = HUMEDAD_BASE.get(tipo_suelo, 62.0)

        humedad = round(humedad_base + random.gauss(0, 4.0), 2)
        temp    = round(18.0 + random.gauss(0, 2.5), 2)

        estado_riego = "ON" if humedad < UMBRAL_RIEGO else "OFF"
        motivo = "HUMEDAD_BAJA" if estado_riego == "ON" else "HUMEDAD_OK"
        if estado_riego == "ON":
            riegos_on += 1

        # Insertar en sensor_realtime
        realtime_doc = {
            "lote_id": lote_id,
            "humedad": humedad,
            "temperatura": temp,
            "updated_at": ahora
        }
        try:
            realtime_coll.insert_one(realtime_doc)
            total_docs += 1
        except Exception as e:
            logger.error(f"Error insertando en sensor_realtime para lote {lote_id}: {e}")

        # Insertar en riego_estado
        riego_doc = {
            "lote_id": lote_id,
            "estado": estado_riego,
            "motivo": motivo,
            "updated_at": ahora
        }
        try:
            riego_coll.insert_one(riego_doc)
            total_docs += 1
        except Exception as e:
            logger.error(f"Error insertando en riego_estado para lote {lote_id}: {e}")

        logger.info(
            f"  lote_id={lote_id:2d} ({tipo_suelo}): "
            f"humedad={humedad}% temp={temp}°C → riego {estado_riego}"
        )

    logger.info(f"Listo. {total_docs} documentos cargados, {riegos_on} riegos encendidos.")
    logger.info("Colecciones escritas: sensor_realtime | riego_estado")
    return total_docs, riegos_on


if __name__ == "__main__":
    run_seed()

