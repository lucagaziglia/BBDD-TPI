"""
Seed de MongoDB Atlas — sensor_readings

Inserta documentos de lecturas de sensores IoT para todos los lotes
del DW de AgroPampa S.A. Una lectura cada 15 minutos durante 7 días.

Uso:
    python nosql/mongodb/seed_sensors.py

Requiere en .env:
    MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/agtech_sensors
"""
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

# Parámetros base por tipo de suelo (igual que los seeds SQL)
HUMEDAD_BASE = {
    "franco":            67.0,
    "franco-limoso":     66.0,
    "franco-arcilloso":  64.0,
    "arcilloso":         62.0,
    "arenoso":           54.0,
}

# Lotes reales del DW (id, nombre, tipo_suelo)
LOTES = [
    (1,  "Lote 1 - La Esperanza",  "franco"),
    (2,  "Lote 2 - La Esperanza",  "franco-arcilloso"),
    (3,  "Lote 3 - La Esperanza",  "arcilloso"),
    (4,  "Lote 1 - Norte Junín",   "franco"),
    (5,  "Lote 2 - Norte Junín",   "franco-limoso"),
    (6,  "Lote 1 - Tres Marías",   "franco"),
    (7,  "Lote 2 - Tres Marías",   "arcilloso"),
    (8,  "Lote 3 - Tres Marías",   "franco-arcilloso"),
    (9,  "Lote 1 - La Rinconada",  "franco"),
    (10, "Lote 2 - La Rinconada",  "franco-limoso"),
    (11, "Lote 3 - La Rinconada",  "arenoso"),
    (12, "Lote 1 - Del Paraná",    "franco"),
    (13, "Lote 2 - Del Paraná",    "arcilloso"),
]


def generar_lecturas(lote_id: int, tipo_suelo: str, dias: int = 7) -> list[dict]:
    """
    Genera lecturas sintéticas realistas para un lote.
    Una lectura cada 15 minutos → 96 lecturas por día por lote.
    """
    docs = []
    humedad_base = HUMEDAD_BASE.get(tipo_suelo, 62.0)
    ahora = datetime.utcnow()
    inicio = ahora - timedelta(days=dias)
    ts = inicio

    while ts <= ahora:
        # Variación sinusoidal por hora del día (más frío de madrugada)
        hora = ts.hour
        variacion_temp = 8.0 * (hora - 6) / 18 if 6 <= hora <= 18 else -4.0

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
        logger.error("MONGODB_URI no configurada en .env. Abortando.")
        sys.exit(1)

    client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
    db = client["agtech_sensors"]
    col = db["sensor_readings"]

    # Índices para queries eficientes
    col.create_index([("lote_id", 1), ("timestamp", -1)])
    col.create_index([("timestamp", -1)])
    logger.info("Índices creados en sensor_readings.")

    total = 0
    for lote_id, nombre, tipo_suelo in LOTES:
        docs = generar_lecturas(lote_id, tipo_suelo, dias=7)
        col.insert_many(docs)
        total += len(docs)
        logger.info(f"  {nombre} ({tipo_suelo}): {len(docs)} documentos insertados.")

    logger.info(f"Seed MongoDB completado: {total} documentos totales.")
    logger.info(f"Colección: agtech_sensors.sensor_readings")
    client.close()


if __name__ == "__main__":
    run_seed()
