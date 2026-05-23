# Cassandra — Capa NoSQL del Datawarehouse

Cassandra reemplaza la dupla **MongoDB + Redis** que usábamos antes. En vez de
mantener dos motores con responsabilidades distintas, modelamos los dos
patrones de acceso (histórico time-series + estado caliente con expiración) en
**tablas separadas del mismo keyspace**.

## Por qué un solo motor

| Caso de uso          | Antes (motor)        | Ahora (tabla Cassandra)         |
|----------------------|----------------------|---------------------------------|
| Histórico crudo IoT  | MongoDB `sensor_readings` | `sensor_readings` (PK por `lote_id` + clustering por `timestamp DESC`) |
| Último valor sensor  | Redis `sensor:{id}:*` | `sensor_realtime` con `default_time_to_live = 3600` |
| Estado de riego      | Redis `riego:{id}:estado` | `riego_estado` con `default_time_to_live = 3600` |
| Alertas efímeras     | Redis `alerta:{id}` (SETEX) | `alertas` con `default_time_to_live = 7200` |

Cassandra es buena en los dos extremos porque:

- Para **time-series** el modelo wide-row (partición por entidad, clustering
  por tiempo) da slice queries por rango de fechas sin índice secundario.
- Para **estado caliente** una tabla con `default_time_to_live` y PK simple se
  comporta como un key-value con expiración: lecturas y escrituras O(1) y las
  filas se borran solas si dejan de actualizarse, igual que `SETEX` de Redis.

## Estructura de archivos

```
nosql/cassandra/
├── schema.cql        # DDL completo del keyspace y las 4 tablas
├── seed_sensors.py   # Carga histórico (reemplaza nosql/mongodb/seed_sensors.py)
├── seed_realtime.py  # Carga estado caliente (reemplaza nosql/redis/seed_realtime.py)
└── README.md         # Este archivo
```

## Cómo levantar el entorno

### Opción A — Cassandra local con Docker

```bash
docker run -d --name cassandra-agtech -p 9042:9042 cassandra:5
# Esperar ~30s a que termine de bootear
docker exec -i cassandra-agtech cqlsh < nosql/cassandra/schema.cql
```

### Opción B — Astra DB (Cassandra managed)

1. Crear DB en https://astra.datastax.com
2. Descargar el "Secure Connect Bundle"
3. Configurar en `.env`:

```bash
ASTRA_DB_SECURE_BUNDLE_PATH=/ruta/al/secure-connect-bundle.zip
ASTRA_DB_CLIENT_ID=...
ASTRA_DB_CLIENT_SECRET=...
CASSANDRA_KEYSPACE=agtech_nosql
```

## Variables de entorno

| Variable                       | Default          | Descripción                                   |
|--------------------------------|------------------|-----------------------------------------------|
| `CASSANDRA_HOSTS`              | `127.0.0.1`      | Contact points separados por coma             |
| `CASSANDRA_PORT`               | `9042`           | Puerto CQL                                    |
| `CASSANDRA_KEYSPACE`           | `agtech_nosql`   | Keyspace a usar                               |
| `CASSANDRA_USERNAME`           | _vacío_          | Usuario (si la instancia tiene auth)          |
| `CASSANDRA_PASSWORD`           | _vacío_          | Password                                      |
| `ASTRA_DB_SECURE_BUNDLE_PATH`  | _vacío_          | Path al secure-bundle para Astra DB           |
| `ASTRA_DB_CLIENT_ID`           | _vacío_          | Client ID de Astra                            |
| `ASTRA_DB_CLIENT_SECRET`       | _vacío_          | Client secret de Astra                        |

Si `ASTRA_DB_SECURE_BUNDLE_PATH` está definido se conecta a Astra; si no,
intenta `CASSANDRA_HOSTS`. Si ninguna está disponible, el ETL cae a **datos
mock** para permitir correr la pipeline sin depender de infra externa.

## Ejecutar los seeds

```bash
# 1) Crear keyspace y tablas (una sola vez por entorno)
cqlsh -f nosql/cassandra/schema.cql

# 2) Cargar histórico (25 lotes × 30 días × 24 lecturas/día ≈ 18.000 filas)
python nosql/cassandra/seed_sensors.py

# 3) Cargar snapshot real-time (sensor_realtime + riego_estado, TTL 1h)
python nosql/cassandra/seed_realtime.py
```

## Patrones de queries soportados

```sql
-- Última hora del lote 12
SELECT * FROM sensor_readings
WHERE lote_id = 12 AND timestamp > '2025-01-20T13:00:00';

-- Snapshot actual de un lote
SELECT humedad, temperatura, updated_at FROM sensor_realtime
WHERE lote_id = 12;

-- Estado de riego
SELECT estado, motivo FROM riego_estado WHERE lote_id = 12;
```

Lo que **no** se debe hacer (anti-patrones Cassandra):

- `SELECT … WHERE timestamp > X` sin `lote_id`: requiere `ALLOW FILTERING` y
  hace full-scan. Si se necesita ese acceso, conviene materializar otra tabla
  particionada por bucket de fecha.
- `SELECT COUNT(*) FROM sensor_readings`: caro, hace scan cross-partition.
  Para conteos usar la base SQL (Supabase) que ya tiene los agregados.
