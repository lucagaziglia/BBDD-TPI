"""
Extractor de MongoDB Atlas.

ETL — Fase EXTRACT:
Lee documentos crudos de la colección `sensor_readings` para un rango de fechas.
No transforma ni filtra nada: retorna los documentos tal cual vienen de MongoDB.
Los datos crudos son lecturas de sensores cada 15 minutos por lote.
"""
import os
import logging
import certifi
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
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
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
