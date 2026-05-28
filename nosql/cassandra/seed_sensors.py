"""
Carga del histórico crudo de lecturas IoT en Cassandra (tabla sensor_readings).

Equivalente al viejo `nosql/mongodb/seed_sensors.py`. Genera ~18.000 filas
(25 lotes × 30 días × 24 lecturas/día) simulando una lectura por hora ininte-
rrumpida durante 30 días.

Modelo de datos en Cassandra:
    PRIMARY KEY (lote_id, timestamp)  WITH CLUSTERING ORDER BY (timestamp DESC)

    - Particionamos por lote_id porque la query típica es
      "dame las últimas N horas del lote X".
    - Clusterizamos por timestamp DESC para que la lectura más reciente quede
      al principio (slice queries baratos).

Las cuatro métricas (temp, humedad_suelo, precipitacion, agua) van en columnas
separadas porque siempre se leen juntas en cada lectura horaria.

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
from etl.extractors.cassandra_extractor import connect_cassandra  # noqa: E402

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# 25 lotes para demostrar escalabilidad — el datawarehouse SQL solo procesa los
# que existen en `dim_campo`/`dim_lote`, los demás llegan al NoSQL pero quedan
# fuera de los agregados. Esto permite dar de alta lotes nuevos sin tocar el
# código de los sensores.
LOTES = list(range(1, 26))


def generate_iot_data(days: int = 30, batch_size: int = 200) -> int:
    """
    Inserta lecturas horarias de los últimos `days` días para los 25 lotes.

    Usa batches CQL acotados (200 statements) para no exceder el límite
    `batch_size_warn_threshold_in_kb` de Cassandra. Cada batch va contra una
    sola partición lógica (un lote), que es la forma idiomática y barata.
    """
    session = connect_cassandra()
    if session is None:
        logger.error("No se pudo conectar a Cassandra. Verificá las variables de entorno.")
        sys.exit(1)

    # Limpiamos para no duplicar — TRUNCATE es la forma idiomática en Cassandra
    # (DELETE sin WHERE no está permitido). Es destructivo, igual que el
    # `delete_many({})` del seed Mongo original.
    logger.info("Truncando sensor_readings…")
    session.execute("TRUNCATE sensor_readings;")

    insert_stmt = session.prepare("""
        INSERT INTO sensor_readings
            (lote_id, timestamp, temp, humedad_suelo, precipitacion, agua)
        VALUES (?, ?, ?, ?, ?, ?)
    """)

    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()
    total = 0

    logger.info(f"Generando histórico de {days} días para {len(LOTES)} lotes…")

    # Importación local: el driver siempre está disponible si connect_cassandra
    # devolvió session != None.
    from cassandra.query import BatchStatement, BatchType

    for lote in LOTES:
        current_time = start_date
        batch = BatchStatement(batch_type=BatchType.UNLOGGED)
        n_in_batch = 0

        while current_time < end_date:
            params = (
                lote,
                current_time,
                round(random.uniform(15, 35), 2),                                       # temp
                round(random.uniform(30, 80), 2),                                       # humedad_suelo
                round(random.uniform(0, 5) if random.random() > 0.8 else 0.0, 2),       # precipitacion
                round(random.uniform(10, 50), 2),                                       # agua
            )
            batch.add(insert_stmt, params)
            n_in_batch += 1
            total += 1
            current_time += timedelta(hours=1)

            if n_in_batch >= batch_size:
                session.execute(batch)
                batch = BatchStatement(batch_type=BatchType.UNLOGGED)
                n_in_batch = 0

        if n_in_batch > 0:
            session.execute(batch)

        logger.info(f"  lote_id={lote:2d}: insertadas {((end_date - start_date).total_seconds() // 3600):.0f} lecturas")

    logger.info(f"Listo. {total} filas insertadas en sensor_readings.")
    session.shutdown()
    return total


if __name__ == "__main__":
    generate_iot_data(days=30)
