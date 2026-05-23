"""
cassandra_extractor.py — Extractor unificado de la capa NoSQL.

Reemplaza a `mongodb_extractor` (histórico) y `redis_extractor` (estado real-time).
Ahora ambos viven en Cassandra, en tablas separadas del mismo keyspace.

Tres responsabilidades:

  1) `connect_cassandra()`     → factory de Session reusada por seeds y ETL.
                                  Soporta Cassandra local (CASSANDRA_HOSTS) y
                                  Astra DB (ASTRA_DB_SECURE_BUNDLE_PATH).

  2) `extract_sensor_readings(desde, hasta)` → reemplaza al extractor Mongo.
                                  Devuelve la misma lista de dicts que antes
                                  para no romper el transformer.

  3) `extract_realtime_state()` → reemplaza al extractor Redis. Devuelve un
                                  dict con el mismo formato `sensor:{id}:tipo`
                                  para no romper consumidores existentes.

Si no hay conexión disponible (sin Cassandra ni Astra configurados, o si la
conexión falla), las dos funciones de extracción caen a datos mock para
permitir correr el pipeline sin depender de infraestructura externa.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────────
# Conexión
# ────────────────────────────────────────────────────────────────────────────

def connect_cassandra():
    """
    Devuelve una `cassandra.cluster.Session` lista para usar o `None` si no
    hay configuración / la conexión falla.

    Prioriza Astra DB si `ASTRA_DB_SECURE_BUNDLE_PATH` está definido; caso
    contrario usa contact points locales vía `CASSANDRA_HOSTS`.
    """
    keyspace = os.getenv("CASSANDRA_KEYSPACE", "agtech")

    try:
        from cassandra.cluster import Cluster
        from cassandra.auth import PlainTextAuthProvider
    except ImportError:
        logger.warning("cassandra-driver no instalado — instalalo con `pip install cassandra-driver`.")
        return None

    # ── Astra DB ────────────────────────────────────────────────────────────
    bundle = os.getenv("ASTRA_DB_SECURE_BUNDLE_PATH")
    if bundle:
        client_id     = os.getenv("ASTRA_DB_CLIENT_ID")
        client_secret = os.getenv("ASTRA_DB_CLIENT_SECRET")
        if not (client_id and client_secret):
            logger.warning("ASTRA_DB_SECURE_BUNDLE_PATH definido pero falta CLIENT_ID/SECRET.")
            return None
        try:
            cluster = Cluster(
                cloud={"secure_connect_bundle": bundle},
                auth_provider=PlainTextAuthProvider(client_id, client_secret),
            )
            session = cluster.connect(keyspace)
            logger.info(f"Conectado a Astra DB (keyspace={keyspace}).")
            return session
        except Exception as e:
            logger.warning(f"Astra DB no disponible ({type(e).__name__}: {e}).")
            return None

    # ── Cassandra local / cluster propio ────────────────────────────────────
    hosts_env = os.getenv("CASSANDRA_HOSTS")
    if not hosts_env:
        logger.info("CASSANDRA_HOSTS no configurado — saltando conexión.")
        return None

    hosts = [h.strip() for h in hosts_env.split(",") if h.strip()]
    port  = int(os.getenv("CASSANDRA_PORT", "9042"))
    user  = os.getenv("CASSANDRA_USERNAME")
    pwd   = os.getenv("CASSANDRA_PASSWORD")

    auth = PlainTextAuthProvider(user, pwd) if user and pwd else None

    try:
        cluster = Cluster(contact_points=hosts, port=port, auth_provider=auth)
        session = cluster.connect(keyspace)
        logger.info(f"Conectado a Cassandra ({hosts}:{port}, keyspace={keyspace}).")
        return session
    except Exception as e:
        logger.warning(f"Cassandra no disponible ({type(e).__name__}: {e}).")
        return None


# ────────────────────────────────────────────────────────────────────────────
# Mock data — fallback cuando no hay infra disponible
# ────────────────────────────────────────────────────────────────────────────

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

_HUMEDAD_BASE = {
    "Franco":           68.0,
    "Franco limoso":    66.0,
    "Franco arcilloso": 64.0,
    "Arcilloso":        62.0,
    "Arenoso":          54.0,
    "Vertisol":         70.0,
}


def _generate_mock_readings(n_dias: int = 7) -> list[dict]:
    """
    Lecturas sintéticas con la misma estructura que devuelve la query a
    `sensor_readings` en Cassandra. Útil para tests y demo offline.

    Las fechas se anclan a "ahora" (en lugar de una fecha fija) para que el
    pipeline real, que filtra por `datetime.now() - N días`, siempre encuentre
    datos en el rango pedido. Si las anclamos a una fecha fija (p. ej.
    2025-06-28) y corremos el ETL meses después, el filtro deja todo afuera.
    """
    import random
    docs = []
    ahora  = datetime.now().replace(minute=0, second=0, microsecond=0)
    inicio = ahora - timedelta(days=n_dias)

    for lote_id, tipo_suelo in _LOTE_TIPO_SUELO.items():
        humedad_base = _HUMEDAD_BASE.get(tipo_suelo, 62.0)
        ts = inicio
        while ts <= ahora:
            hora = ts.hour
            var_temp = 8.0 * abs(hora - 14) / 14 * (-1 if hora < 14 else 1)
            docs.append({
                "lote_id":       lote_id,
                "timestamp":     ts,
                "temp":          round(18.0 + var_temp + random.gauss(0, 1.2), 2),
                "humedad_suelo": round(humedad_base + random.gauss(0, 3.5), 2),
                "precipitacion": round(random.uniform(0, 5) if random.random() > 0.8 else 0.0, 2),
                "agua":          round(random.uniform(10, 50), 2),
            })
            ts += timedelta(hours=1)
    return docs


MOCK_READINGS: list[dict] = _generate_mock_readings(n_dias=30)

MOCK_STATE: dict[str, str] = {
    "sensor:1:humedad":     "62.3",
    "sensor:1:temperatura": "21.4",
    "sensor:2:humedad":     "45.1",
    "sensor:2:temperatura": "23.0",
    "sensor:3:humedad":     "71.5",
    "sensor:3:temperatura": "19.8",
    "riego:1:estado":       "ON",
    "riego:2:estado":       "OFF",
    "riego:3:estado":       "OFF",
}


# ────────────────────────────────────────────────────────────────────────────
# Extractores
# ────────────────────────────────────────────────────────────────────────────

def extract_sensor_readings(desde: datetime, hasta: datetime, session=None) -> list[dict]:
    """
    Extrae las lecturas crudas de `sensor_readings` entre `desde` y `hasta`.

    Cassandra requiere filtrar por la partición (`lote_id`), así que iteramos
    sobre los 25 lotes haciendo una slice query por lote. Cada slice es
    eficiente porque las filas están clusterizadas por `timestamp DESC`.

    Devuelve la misma estructura que el viejo extractor Mongo:
        [{"lote_id": int, "timestamp": dt, "temp": float,
          "humedad_suelo": float, "precipitacion": float, "agua": float}, …]
    """
    own_session = False
    if session is None:
        session = connect_cassandra()
        own_session = True

    if session is None:
        logger.warning("Cassandra no disponible — usando datos mock para testing.")
        return _filter_by_date(MOCK_READINGS, desde, hasta)

    try:
        # PreparedStatement reutilizable: una sola compilación, N ejecuciones.
        stmt = session.prepare("""
            SELECT lote_id, timestamp, temp, humedad_suelo, precipitacion, agua
            FROM sensor_readings
            WHERE lote_id = ? AND timestamp >= ? AND timestamp <= ?
        """)

        logger.info(f"Extrayendo de Cassandra: {desde} → {hasta}")
        readings: list[dict] = []

        # Iteramos sobre los lotes conocidos. Si en el futuro queremos descubrirlos
        # dinámicamente, conviene materializar una tabla `lotes_activos` para no
        # depender de un full-scan de `sensor_readings`.
        for lote_id in _LOTE_TIPO_SUELO.keys():
            rows = session.execute(stmt, (lote_id, desde, hasta))
            for row in rows:
                readings.append({
                    "lote_id":       row.lote_id,
                    "timestamp":     row.timestamp,
                    "temp":          row.temp,
                    "humedad_suelo": row.humedad_suelo,
                    "precipitacion": row.precipitacion,
                    "agua":          row.agua,
                })

        logger.info(f"Extraídas {len(readings)} filas desde sensor_readings.")
        return readings

    except Exception as e:
        logger.warning(f"Error consultando Cassandra ({type(e).__name__}: {e}). Cayendo a mock.")
        return _filter_by_date(MOCK_READINGS, desde, hasta)
    finally:
        if own_session and session is not None:
            try:
                session.shutdown()
            except Exception:
                pass


def extract_realtime_state(session=None) -> dict[str, str]:
    """
    Extrae el snapshot caliente de `sensor_realtime` + `riego_estado`.

    Para preservar la API del consumidor anterior (que recibía un dict con
    claves estilo `sensor:{id}:humedad`), aplastamos las dos tablas en ese
    mismo formato. Así no hay que tocar nada río abajo.
    """
    own_session = False
    if session is None:
        session = connect_cassandra()
        own_session = True

    if session is None:
        logger.warning("Cassandra no disponible — usando datos mock para testing.")
        return dict(MOCK_STATE)

    try:
        state: dict[str, str] = {}

        # Estos son full-scans de la tabla, pero las tablas son muy chicas
        # (≤ 25 filas) por diseño: una fila por lote. Es O(N_lotes).
        for row in session.execute("SELECT lote_id, humedad, temperatura FROM sensor_realtime"):
            if row.humedad is not None:
                state[f"sensor:{row.lote_id}:humedad"]     = str(row.humedad)
            if row.temperatura is not None:
                state[f"sensor:{row.lote_id}:temperatura"] = str(row.temperatura)

        for row in session.execute("SELECT lote_id, estado FROM riego_estado"):
            if row.estado is not None:
                state[f"riego:{row.lote_id}:estado"] = row.estado

        logger.info(f"Extraídas {len(state)} entradas de estado caliente desde Cassandra.")
        return state

    except Exception as e:
        logger.error(f"Error extrayendo estado real-time de Cassandra: {e}")
        return {}
    finally:
        if own_session and session is not None:
            try:
                session.shutdown()
            except Exception:
                pass


# ────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ────────────────────────────────────────────────────────────────────────────

def _filter_by_date(docs: list[dict], desde: datetime, hasta: datetime) -> list[dict]:
    """Filtra los mock readings por rango de fechas para imitar la slice query."""
    return [d for d in docs if desde <= d["timestamp"] <= hasta]
