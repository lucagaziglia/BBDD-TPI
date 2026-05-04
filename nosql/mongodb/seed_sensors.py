import os
import sys
import random
import logging
import certifi
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

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
    (1,  "Lote C",                "Arcilloso",        "Pergamino"),
    (2,  "Lote B",                "Franco arcilloso", "Pergamino"),
    (3,  "Lote A",                "Franco limoso",    "Pergamino"),
    (4,  "Lote 3 - La Rinconada", "Arenoso",          "Pergamino"),
    (5,  "Lote 2 - Laguna",       "Franco arcilloso", "Pergamino"),
    (6,  "Lote 1 - Arroyo",       "Franco limoso",    "Pergamino"),
    (7,  "Lote 2 - Sur",          "Arcilloso",        "Junín"),
    (8,  "Lote 1 - Norte",        "Franco limoso",    "Junín"),
    (9,  "Lote 4 (San Cayetano)", "Arcilloso",        "Nueve de Julio"),
    (10, "Lote 3 (San Cayetano)", "Franco limoso",    "Nueve de Julio"),
    (11, "Lote 2 (San Cayetano)", "Arenoso",          "Nueve de Julio"),
    (12, "Lote 1 (San Cayetano)", "Franco limoso",    "Nueve de Julio"),
    (13, "Lote 4 (Barrancosa)",   "Franco limoso",    "Rosario"),
    (14, "Lote 3 (Barrancosa)",   "Arenoso",          "Rosario"),
    (15, "Lote 2 (Barrancosa)",   "Vertisol",         "Rosario"),
    (16, "Lote 1 (Barrancosa)",   "Vertisol",         "Rosario"),
    (17, "Lote 2 - Secundario",   "Franco limoso",    "Venado Tuerto"),
    (18, "Lote 1 - Principal",    "Franco arcilloso", "Venado Tuerto"),
    (19, "Lote 3 - Centro",       "Arcilloso",        "Venado Tuerto"),
    (20, "Lote 2 - Oeste",        "Franco arcilloso", "Venado Tuerto"),
    (21, "Lote 1 - Este",         "Franco limoso",    "Venado Tuerto"),
    (22, "Lote Sur",              "Arcilloso",        "Córdoba Capital"),
    (23, "Lote Norte",            "Franco limoso",    "Córdoba Capital"),
    (24, "Lote 2 (El Retiro)",    "Vertisol",         "Río Cuarto"),
    (25, "Lote 1 (El Retiro)",    "Franco limoso",    "Río Cuarto"),
]


def generar_lecturas(lote_id: int, tipo_suelo: str, dias: int = 7) -> list[dict]:
    docs = []
    humedad_base = HUMEDAD_BASE.get(tipo_suelo, 62.0)

    ahora = datetime.utcnow()
    inicio = ahora - timedelta(days=dias)
    ts = inicio

    while ts <= ahora:
        hora = ts.hour
        if 6 <= hora <= 18:
            variacion_temp = 8.0 * (hora - 6) / 18
        else:
            variacion_temp = -4.0

        docs.append({
            "lote_id":      lote_id,
            "tipo_suelo":   tipo_suelo,
            "timestamp":    ts,
            "tipo_lectura": "HUMEDAD_SUELO",
            "valor":        round(humedad_base + random.gauss(0, 3.5), 2),
            "unidad":       "%",
        })
        docs.append({
            "lote_id":      lote_id,
            "tipo_suelo":   tipo_suelo,
            "timestamp":    ts,
            "tipo_lectura": "TEMPERATURA",
            "valor":        round(18.0 + variacion_temp + random.gauss(0, 1.2), 2),
            "unidad":       "°C",
        })
        ts += timedelta(minutes=15)

    return docs


def run_seed():
    uri = os.getenv("MONGODB_URI")
    if not uri:
        logger.error("MONGODB_URI no está en .env. Cortamos acá.")
        sys.exit(1)

    client = MongoClient(uri, serverSelectionTimeoutMS=10000, tlsCAFile=certifi.where())
    db = client["agtech_sensors"]
    col = db["sensor_readings"]

    deleted = col.delete_many({}).deleted_count
    if deleted:
        logger.info(f"Limpiamos la colección: {deleted} docs viejos al tacho.")

    col.create_index([("lote_id", 1), ("timestamp", -1)])
    col.create_index([("timestamp", -1)])
    logger.info("Índices listos.")

    total = 0
    for lote_id, nombre, tipo_suelo, localidad in LOTES:
        docs = generar_lecturas(lote_id, tipo_suelo, dias=7)
        col.insert_many(docs)
        total += len(docs)
        logger.info(f"  lote_id={lote_id:2d} ({localidad}, {tipo_suelo}): {len(docs)} docs.")

    logger.info(f"Listo. {total} documentos cargados en agtech_sensors.sensor_readings")
    client.close()


if __name__ == "__main__":
    run_seed()
