"""
Extractor de MongoDB.
Se conecta a MongoDB Atlas para recuperar los registros históricos de sensores
(colección sensor_readings) para un período de tiempo determinado.
"""
import os
import logging
from pymongo import MongoClient
from datetime import datetime

logger = logging.getLogger(__name__)

def extract_sensor_readings(desde: datetime, hasta: datetime) -> list[dict]:
    """
    Extrae lecturas de sensores de MongoDB Atlas entre las fechas dadas.
    Retorna lista de documentos crudos sin transformar.
    """
    uri = os.getenv("MONGODB_URI")
    if not uri:
        logger.warning("MONGODB_URI no está configurada. Retornando datos mockeados para testing.")
        # Mock para testing si no hay credenciales
        return [
            {"sensor_id": "S1", "lote_id": 1, "timestamp": desde, "tipo_lectura": "HUMEDAD_SUELO", "valor": 25.5},
            {"sensor_id": "S1", "lote_id": 1, "timestamp": hasta, "tipo_lectura": "TEMPERATURA", "valor": 22.1}
        ]
    
    try:
        client = MongoClient(uri)
        db = client.get_database()
        collection = db["sensor_readings"]
        
        query = {
            "timestamp": {
                "$gte": desde,
                "$lte": hasta
            }
        }
        
        logger.info(f"Extrayendo datos de MongoDB desde {desde} hasta {hasta}")
        cursor = collection.find(query)
        readings = list(cursor)
        logger.info(f"Se extrajeron {len(readings)} documentos de MongoDB.")
        return readings
    except Exception as e:
        logger.error(f"Error extrayendo de MongoDB: {e}")
        return []
