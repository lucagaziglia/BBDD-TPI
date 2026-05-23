-- ============================================================================
-- Cassandra — Esquema completo de la capa NoSQL del Datawarehouse AgroPampa
-- ============================================================================
--
-- Cassandra reemplaza la combinación previa MongoDB + Redis. Con un único motor
-- cubrimos los dos casos de uso:
--
--   1) Persistencia cruda de lecturas de sensores IoT (histórico time-series).
--      → Antes vivía en MongoDB (colección `sensor_readings`).
--   2) Snapshot del "último estado" de cada lote con expiración automática.
--      → Antes vivía en Redis (`sensor:{id}:*`, `riego:{id}:estado`) con TTL.
--
-- ¿Por qué Cassandra para los dos? Porque modela ambos patrones de forma natural:
--
--   - Para histórico: particionamos por `lote_id` y clusterizamos por timestamp,
--     lo que da lecturas y escrituras O(log N) por partición y rangos de tiempo
--     eficientes (slice queries) sin necesidad de índices secundarios.
--
--   - Para estado caliente: una sola fila por lote (PK = lote_id) y
--     `default_time_to_live = 3600` para que las filas se borren solas al cabo
--     de 1 hora si dejan de actualizarse. Equivalente funcional a `SETEX` de
--     Redis, sin necesidad de un segundo motor.
--
-- Cómo correrlo:
--     cqlsh -f nosql/cassandra/schema.cql
-- ============================================================================


-- ── Keyspace ────────────────────────────────────────────────────────────────
-- SimpleStrategy con RF=1 alcanza para entorno académico / single-node.
-- En producción se cambiaría por NetworkTopologyStrategy con RF=3 por DC.
CREATE KEYSPACE IF NOT EXISTS agtech_nosql
WITH REPLICATION = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

USE agtech_nosql;


-- ── 1. Histórico crudo de sensores (reemplaza MongoDB) ──────────────────────
--
-- Modelo de query: "Dame todas las lecturas del lote X entre T1 y T2".
--   PARTITION KEY  → lote_id  (todas las lecturas del lote viven juntas)
--   CLUSTERING KEY → timestamp DESC  (la más reciente queda primero)
--
-- Las cuatro métricas (temp, humedad_suelo, precipitacion, agua) se guardan
-- en columnas separadas porque siempre se leen juntas en cada lectura horaria.
-- Esto es equivalente al documento que Mongo guardaba en `sensor_readings`.
CREATE TABLE IF NOT EXISTS sensor_readings (
    lote_id        int,
    timestamp      timestamp,
    temp           double,
    humedad_suelo  double,
    precipitacion  double,
    agua           double,
    PRIMARY KEY (lote_id, timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC)
  AND comment = 'Histórico crudo de lecturas IoT — reemplaza la colección Mongo sensor_readings';


-- ── 2. Estado caliente de sensores (reemplaza Redis sensor:*) ───────────────
--
-- Una sola fila por lote con los últimos valores observados.
-- El TTL global de 3600s emula el comportamiento de SETEX de Redis: si un
-- sensor deja de reportar, la fila desaparece sola y el dashboard ve "Offline"
-- en lugar de un valor congelado.
--
-- Como Cassandra hace UPSERT por defecto (INSERT == UPDATE sobre la PK), re-
-- ejecutar la carga simplemente sobrescribe el valor y reinicia el TTL,
-- mismo comportamiento que el `SET ex=3600` de Redis.
CREATE TABLE IF NOT EXISTS sensor_realtime (
    lote_id      int PRIMARY KEY,
    humedad      double,
    temperatura  double,
    updated_at   timestamp
) WITH default_time_to_live = 3600
  AND comment = 'Última lectura por lote con TTL 1h — reemplaza Redis sensor:{id}:*';


-- ── 3. Estado del sistema de riego (reemplaza Redis riego:*) ────────────────
--
-- El sistema de riego automático lee esto cada pocos segundos para decidir si
-- abrir o cerrar la canilla. Conviene tenerlo separado de `sensor_realtime`
-- porque tiene cadencia distinta (cambia menos seguido) y consumidores
-- distintos (controlador de actuadores vs. dashboard).
CREATE TABLE IF NOT EXISTS riego_estado (
    lote_id      int PRIMARY KEY,
    estado       text,       -- 'ON' | 'OFF'
    motivo       text,       -- por qué se activó/desactivó (humedad baja, manual, etc.)
    updated_at   timestamp
) WITH default_time_to_live = 3600
  AND comment = 'Estado actual del riego por lote con TTL 1h — reemplaza Redis riego:{id}:estado';


-- ── 4. Alertas efímeras (opcional, antes Redis con SETEX) ───────────────────
--
-- Particionamos por lote_id para que el dashboard pueda traerse las alertas
-- de un lote con un solo seek a disco. TTL 2h porque las alertas son más
-- "longevas" que un valor de sensor pero igual deben caducar.
CREATE TABLE IF NOT EXISTS alertas (
    lote_id    int,
    timestamp  timestamp,
    tipo       text,
    mensaje    text,
    PRIMARY KEY (lote_id, timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC)
  AND default_time_to_live = 7200
  AND comment = 'Alertas activas por lote (TTL 2h) — reemplaza Redis alerta:{id}';
