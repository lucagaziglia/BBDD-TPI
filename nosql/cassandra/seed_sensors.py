"""
Carga del histórico crudo de lecturas IoT en Astra DB (colección sensor_readings).

Genera ~18.000 documentos (25 lotes × 30 días × 24 lecturas/día) simulando una
lectura por hora ininterrumpida durante 30 días.

Estructura de documento:
    {
        "lote_id": int,
        "timestamp": string (ISO 8601),
        "temp": float,
        "humedad_suelo": float,
        "precipitacion": float,
        "agua": float
    }

Correr con:
    python nosql/cassandra/seed_sensors.py
"""
import os
import sys
import random
import logging
from datetime import datetime, timedelta

from dotenv import load_dotenv

# Permite importar el helper de conexión desde el extractor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from etl.extractors.cassandra_extractor import connect_astradb  # noqa: E402

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 25 lotes
LOTES = list(range(1, 26))


def generate_iot_data(days: int = 30, batch_size: int = 100) -> int:
    """
    Inserta lecturas horarias de los últimos `days` días para los 25 lotes.
    
    Usa batches acotados para eficiencia.
    """
    collection = connect_astradb("sensor_readings")
    if collection is None:
        logger.error("No se pudo conectar a Astra DB. Verificá las variables de entorno.")
        sys.exit(1)

    # Limpiamos para no duplicar
    logger.info("Limpiando sensor_readings…")
    collection.delete_many({})

    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()
    total = 0

    logger.info(f"Generando histórico de {days} días para {len(LOTES)} lotes…")

    for lote in LOTES:
        docs = []
        current_time = start_date

        while current_time < end_date:
            doc = {
                "lote_id": lote,
                "timestamp": current_time.replace(microsecond=0).isoformat() + "Z",
                "temp": round(random.uniform(15, 35), 2),
                "humedad_suelo": round(random.uniform(30, 80), 2),
                "precipitacion": round(random.uniform(0, 5) if random.random() > 0.8 else 0.0, 2),
                "agua": round(random.uniform(10, 50), 2),
            }
            docs.append(doc)
            total += 1
            current_time += timedelta(hours=1)

            # Insert en batches
            if len(docs) >= batch_size:
                try:
                    collection.insert_many(docs)
                    docs = []
                except Exception as e:
                    logger.error(f"Error insertando batch para lote {lote}: {e}")
                    return -1

        # Insertar docs restantes
        if docs:
            try:
                collection.insert_many(docs)
            except Exception as e:
                logger.error(f"Error insertando batch final para lote {lote}: {e}")
                return -1

        n_readings = ((end_date - start_date).total_seconds() // 3600)
        logger.info(f"  lote_id={lote:2d}: insertadas {n_readings:.0f} lecturas")

    logger.info(f"Listo. {total} documentos insertados en sensor_readings.")
    return total


if __name__ == "__main__":
    generate_iot_data(days=30)
