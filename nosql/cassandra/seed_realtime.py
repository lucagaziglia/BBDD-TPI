"""
Carga del "estado actual" de los sensores en Cassandra (tablas sensor_realtime
y riego_estado).

Equivalente al viejo `nosql/redis/seed_realtime.py`. La diferencia clave es que
ya NO usamos Redis: el TTL ahora lo provee Cassandra a nivel tabla
(`default_time_to_live = 3600`).

¿POR QUÉ TTL?
    Si un sensor falla y deja de reportar, la fila desaparece sola al cabo de
    1 hora y el dashboard ve "Offline" en lugar de un valor congelado. Es el
    mismo razonamiento que teníamos con `SETEX` en Redis — solo cambió el motor.

COMPORTAMIENTO AL RE-EJECUTAR:
    Cassandra hace UPSERT por defecto (INSERT == UPDATE sobre la PK). Cada vez
    que corre este script se sobrescriben los valores y se reinicia el reloj
    del TTL. Ideal para simular cambios de estado en vivo durante una demo.

CAPAS DE DATOS (con la nueva arquitectura):
    - Cassandra sensor_realtime / riego_estado : capa de velocidad (TTL 1h).
    - Cassandra sensor_readings                : capa de persistencia cruda.
    - Supabase (PostgreSQL)                    : capa analítica (datos diarios).

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
from etl.extractors.cassandra_extractor import connect_cassandra  # noqa: E402

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# Humedad esperada según tipo de suelo (mismo modelo que el seed Redis original).
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
    session = connect_cassandra()
    if session is None:
        logger.error("No se pudo conectar a Cassandra. Verificá las variables de entorno.")
        sys.exit(1)

    insert_realtime = session.prepare("""
        INSERT INTO sensor_realtime (lote_id, humedad, temperatura, updated_at)
        VALUES (?, ?, ?, ?)
    """)
    insert_riego = session.prepare("""
        INSERT INTO riego_estado (lote_id, estado, motivo, updated_at)
        VALUES (?, ?, ?, ?)
    """)

    ahora = datetime.utcnow()
    total_filas = 0
    riegos_on = 0

    for lote_id, _nombre, tipo_suelo in LOTES:
        humedad_base = HUMEDAD_BASE.get(tipo_suelo, 62.0)

        humedad = round(humedad_base + random.gauss(0, 4.0), 2)
        temp    = round(18.0 + random.gauss(0, 2.5), 2)

        estado_riego = "ON" if humedad < UMBRAL_RIEGO else "OFF"
        motivo = "HUMEDAD_BAJA" if estado_riego == "ON" else "HUMEDAD_OK"
        if estado_riego == "ON":
            riegos_on += 1

        session.execute(insert_realtime, (lote_id, humedad, temp, ahora))
        session.execute(insert_riego,    (lote_id, estado_riego, motivo, ahora))
        total_filas += 2

        logger.info(
            f"  lote_id={lote_id:2d} ({tipo_suelo}): "
            f"humedad={humedad}% temp={temp}°C → riego {estado_riego}"
        )

    logger.info(f"Listo. {total_filas} filas cargadas, {riegos_on} riegos encendidos.")
    logger.info("Tablas escritas: sensor_realtime | riego_estado (TTL 3600s)")
    session.shutdown()
    return total_filas, riegos_on


if __name__ == "__main__":
    run_seed()
