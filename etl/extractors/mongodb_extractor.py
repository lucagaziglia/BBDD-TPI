import os
import random
import logging
import certifi
from pymongo import MongoClient
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

_HUMEDAD_BASE = {
    "Franco":           68.0,
    "Franco limoso":    66.0,
    "Franco arcilloso": 64.0,
    "Arcilloso":        62.0,
    "Arenoso":          54.0,
    "Vertisol":         70.0,
}

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


def _generate_mock_readings(n_dias: int = 7) -> list[dict]:
    docs = []
    ahora = datetime(2025, 6, 28, 23, 0, 0)
    inicio = ahora - timedelta(days=n_dias)

    for lote_id, tipo_suelo in _LOTE_TIPO_SUELO.items():
        humedad_base = _HUMEDAD_BASE.get(tipo_suelo, 62.0)
        ts = inicio
        while ts <= ahora:
            hora = ts.hour
            var_temp = 8.0 * abs(hora - 14) / 14 * (-1 if hora < 14 else 1)
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
                "valor":        round(18.0 + var_temp + random.gauss(0, 1.2), 2),
                "unidad":       "°C",
            })
            ts += timedelta(hours=1)  
    return docs


MOCK_READINGS: list[dict] = _generate_mock_readings(n_dias=7)


def extract_sensor_readings(desde: datetime, hasta: datetime) -> list[dict]:
    uri = os.getenv("MONGODB_URI")
    if not uri:
        logger.warning("MONGODB_URI no configurada — usando datos mock para testing.")
        return MOCK_READINGS

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
        db = client["agtech_sensors"]
        collection = db["sensor_readings"]

        query = {"timestamp": {"$gte": desde, "$lte": hasta}}
        logger.info(f"Extrayendo de MongoDB: {desde} → {hasta}")
        readings = list(collection.find(query))
        logger.info(f"Extraídos {len(readings)} documentos.")
        client.close()
        return readings

    except Exception as e:
        logger.warning(f"MongoDB no disponible ({type(e).__name__}). Usando datos mock.")
        return MOCK_READINGS
