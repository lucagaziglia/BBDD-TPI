# AgTech Datawarehouse - TP Final BBDD

Bienvenido al repositorio del Trabajo Práctico Final de la materia Bases de Datos (UNSAM).

## Arquitectura de datos

```
              ┌──────────────────────┐
   IoT  ─────►│ Cassandra (NoSQL)    │── sensor_readings   (histórico time-series)
              │                      │── sensor_realtime   (estado caliente, TTL 1h)
              │                      │── riego_estado      (control de actuadores, TTL 1h)
              │                      │── alertas           (alertas efímeras, TTL 2h)
              └──────────┬───────────┘
                         │  ETL (Python)
                         ▼
              ┌──────────────────────┐
              │ Supabase / Postgres  │── modelo dimensional (SQL DW)
              └──────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Dashboard BI         │── Chart.js
              └──────────────────────┘
```

> Cambió la capa NoSQL: antes teníamos **MongoDB + Redis**, ahora la
> reemplazamos por **una única instancia de Cassandra** que cubre los dos casos
> de uso. Detalles en [nosql/cassandra/README.md](nosql/cassandra/README.md).

## Setup e Instrucciones

1. **Clonar repositorio e instalar dependencias:**
   ```bash
   git clone <repo_url>
   cd BBDD-TPI
   pip install -r requirements.txt
   ```

2. **Configuración de Variables de Entorno:**
   Copiá `.env.example` a `.env` y completá con las credenciales:
   - Supabase (PostgreSQL): `SUPABASE_URL`, `SUPABASE_ANON_KEY`
   - Cassandra local: `CASSANDRA_HOSTS`, `CASSANDRA_PORT`, `CASSANDRA_KEYSPACE`
   - O Astra DB: `ASTRA_DB_SECURE_BUNDLE_PATH`, `ASTRA_DB_CLIENT_ID`, `ASTRA_DB_CLIENT_SECRET`
   ```bash
   cp .env.example .env
   ```

3. **Levantar Cassandra (si vas con Docker local):**
   ```bash
   docker run -d --name cassandra-agtech -p 9042:9042 cassandra:5
   # esperar ~30s a que termine de bootear
   docker exec -i cassandra-agtech cqlsh < nosql/cassandra/schema.cql
   python nosql/cassandra/seed_sensors.py
   python nosql/cassandra/seed_realtime.py
   ```

4. **Ejecutar el Pipeline ETL:**
   ```bash
   python etl/pipeline.py
   ```
   Si no hay Cassandra disponible, el pipeline cae a datos mock para que las
   pruebas y la demo corran sin infra externa.

Para más contexto y convenciones, leé el archivo `CLAUDE.md`.

## NoSQL — Estructura

```
nosql/cassandra/
├── schema.cql        # DDL: keyspace + 4 tablas
├── seed_sensors.py   # Carga ~18.000 lecturas históricas (25 lotes × 30 días × 24h)
├── seed_realtime.py  # Carga snapshot real-time con TTL 1h
└── README.md         # Diseño, decisiones y patrones de query
```

## SQL — Orden de ejecución

La carpeta `sql/` contiene el modelo dimensional completo. Ejecutar en este orden:

```
# 1. Schema (DDL) — crear tablas vacías
sql/schema/01_dimensions_leaf.sql        # dim_provincia, dim_tipo_cultivo, dim_propietario, dim_tiempo
sql/schema/02_dimensions_intermediate.sql # dim_localidad, dim_campo, dim_cultivo, dim_maquinaria
sql/schema/03_dimensions_main.sql        # dim_lote, dim_clima
sql/schema/04_fact.sql                   # fact_produccion

# 2. Seeds — poblar con datos sintéticos
sql/seeds/01_seed_provincias.sql
sql/seeds/02_seed_tipos.sql
sql/seeds/03_seed_propietarios.sql
sql/seeds/04_seed_localidades.sql
sql/seeds/05_seed_campos.sql
sql/seeds/06_seed_lotes.sql
sql/seeds/07_seed_cultivos_maquinaria.sql
sql/seeds/08_seed_tiempo.sql
sql/seeds/09_seed_fact.sql

# 3. Operaciones DML (consigna ítems 4.x)
sql/operations/delete_ejemplo.sql
sql/operations/update_ejemplo.sql
sql/operations/busqueda_1_clave.sql
sql/operations/busqueda_2_claves.sql

# 4. Queries analíticas
sql/queries/bi/rendimiento_por_campania.sql
sql/queries/bi/produccion_por_propietario.sql
sql/queries/mining/segmentacion_lotes.sql
sql/queries/mining/prediccion_rendimiento.sql
```
