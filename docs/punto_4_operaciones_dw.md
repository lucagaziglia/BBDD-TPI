# Punto 4 — Operaciones sobre el Datawarehouse

**AgroPampa S.A. · UNSAM · Bases de Datos · TP Final 2025**

---

## Arquitectura general del ETL

Antes de detallar cada operación, es importante entender cómo funciona el pipeline ETL que conecta los tres motores de almacenamiento con el Datawarehouse.

```
MongoDB Atlas                    Redis Cloud
(sensor_readings)                (sensor:{id}:*)
       │                               │
       ▼                               ▼
extract_sensor_readings()    extract_realtime_state()
       │
       ▼
transform_readings()
       │
       ▼
load_to_dim_clima()
       │
       ▼
dim_clima  ──FK──▶  dim_lote  ──FK──▶  dim_campo  ──FK──▶  dim_propietario
                       │
                       └──FK──▶  dim_tipo_suelo
dim_clima  ──FK──▶  dim_tiempo
```

El pipeline se coordina desde `etl/pipeline.py` y se divide en tres módulos:

| Módulo | Archivo | Responsabilidad |
|--------|---------|-----------------|
| **Extractors** | `etl/extractors/mongodb_extractor.py` | Lectura cruda desde MongoDB Atlas |
| | `etl/extractors/redis_extractor.py` | Lectura del estado actual desde Redis |
| **Transformers** | `etl/transformers/sensor_transformer.py` | Limpieza, validación y agregación |
| **Loaders** | `etl/loaders/supabase_loader.py` | Carga idempotente en Supabase (PostgreSQL) |

---

## Funciones del ETL — descripción de alto nivel

### `run_pipeline(dias)` · `etl/pipeline.py`

Orquesta los tres pasos en orden. Primero consulta a Supabase dos tablas de referencia que necesita el transformer, luego ejecuta Extract → Transform → Load y devuelve un resumen con el conteo de filas en cada paso.

---

### `fetch_tiempo_map()` · `etl/pipeline.py`

Consulta `dim_tiempo` en Supabase y construye un diccionario `{fecha_primer_día_del_mes → tiempo_id}`. Este mapa es el puente entre el mundo de los sensores (timestamps continuos) y el mundo del DW (granularidad mensual). Sin él, el transformer no puede resolver a qué período pertenece cada lectura.

---

### `fetch_lotes_activos()` · `etl/pipeline.py`

Consulta `dim_lote` filtrando `activo = TRUE` y devuelve el conjunto de `lote_id` válidos. Sirve como guardia de integridad referencial: si un sensor envía datos de un lote que fue dado de baja (o que todavía no existe en el DW), esas lecturas se descartan antes de llegar al loader, evitando errores de FK.

---

### `extract_sensor_readings(desde, hasta)` · `etl/extractors/mongodb_extractor.py`

Se conecta a MongoDB Atlas y extrae todos los documentos de la colección `sensor_readings` cuyo `timestamp` cae dentro del período solicitado. Cada documento representa una lectura de un sensor (humedad de suelo o temperatura) en un lote específico. No aplica ninguna transformación: devuelve los documentos exactamente como los almacena MongoDB. Si la conexión falla, retorna un conjunto de datos mock para que el pipeline pueda continuar en modo de prueba.

---

### `extract_realtime_state()` · `etl/extractors/redis_extractor.py`

Lee las keys `sensor:{lote_id}:humedad`, `sensor:{lote_id}:temperatura` y `riego:{lote_id}:estado` de Redis. Estas keys tienen TTL de una hora y representan el *último valor conocido* de cada sensor, no el histórico. Se usa para dashboards en tiempo real y para la lógica de riego automático. A diferencia de MongoDB, esta extracción no se carga en el DW histórico.

---

### `transform_readings(raw_data, tiempo_map, lotes_activos)` · `etl/transformers/sensor_transformer.py`

Es el corazón del pipeline. Recibe la lista cruda de lecturas y produce un DataFrame limpio con exactamente las columnas que necesita `dim_clima`. Las etapas internas son:

1. **Normalización temporal:** convierte cada timestamp al primer día de su mes (`mes_inicio`). Esto alinea las lecturas con la granularidad mensual de `dim_tiempo`.

2. **Filtrado de outliers:** descarta lecturas fuera de rango (`HUMEDAD_SUELO` entre 10–100 %, `TEMPERATURA` entre -10 y 50 °C). Cada tipo se filtra con sus propios límites para no confundir umbrales de humedad con umbrales de temperatura.

3. **Filtrado de lotes:** descarta cualquier lectura cuyo `lote_id` no esté en el set de lotes activos del DW.

4. **Resolución de `tiempo_id`:** usa `tiempo_map` para convertir `mes_inicio` en el `tiempo_id` correspondiente de `dim_tiempo`. Lecturas en meses que no existan en `dim_tiempo` se descartan con un warning.

5. **Agregación mensual:** agrupa por `(lote_id, tiempo_id, tipo_lectura)` y calcula promedio, máximo y mínimo de cada variable.

6. **Pivot y merge:** convierte las filas por tipo de lectura en columnas (`humedad_promedio`, `temp_promedio`, `temp_max`, `temp_min`). Los extremos de temperatura se unen mediante merge para no desalinear filas que solo tienen un tipo de sensor.

7. **Derivación de precipitación:** como los sensores IoT no miden lluvia directamente, `precipitacion_mm` se aproxima a partir de la humedad promedio. Esto es explícitamente un dato sintético.

---

### `load_to_dim_clima(df)` · `etl/loaders/supabase_loader.py`

Recibe el DataFrame transformado y lo carga en `dim_clima` con una estrategia **idempotente en dos pasos**:

1. **DELETE previo:** borra las filas existentes en `dim_clima` para las combinaciones `(lote_id, tiempo_id)` que se van a cargar. Esto garantiza que si el pipeline se corre dos veces sobre el mismo período, los datos no se dupliquen.

2. **INSERT:** inserta los registros nuevos con `clima_id` generado secuencialmente (tomando el máximo actual de la tabla y avanzando desde ahí).

Esta estrategia de DELETE + INSERT es equivalente a un UPSERT y mantiene la integridad con las FKs de `dim_clima`:

```
dim_clima.lote_id   ──▶  dim_lote.lote_id      (el lote debe existir y estar activo)
dim_clima.tiempo_id ──▶  dim_tiempo.tiempo_id   (el mes debe estar en el calendario del DW)
```

---

## 4.a — Creación

### DDL — Tablas creadas

```sql
CREATE TABLE IF NOT EXISTS "dim_lote" (
  "lote_id"       INTEGER,
  "campo_id"      INTEGER,
  "nombre"        VARCHAR(50),
  "superficie_ha" DECIMAL(10,2),
  "tipo_suelo_id" INTEGER,
  "coordenadas"   VARCHAR(255),
  "activo"        BOOLEAN,
  "created_at"    TIMESTAMP,
  "updated_at"    TIMESTAMP,
  PRIMARY KEY("lote_id")
);

CREATE TABLE IF NOT EXISTS "fact_produccion" (
  "id"                      INTEGER,
  "maquinaria_id"           INTEGER,
  "cultivo_id"              INTEGER,
  "lote_id"                 INTEGER,
  "tiempo_id"               INTEGER,
  "rendimiento_kg_ha"       NUMERIC,
  "superficie_cosechada_ha" NUMERIC,
  "costo_total"             DECIMAL(10,2),
  "previo_venta_tn_prom"    NUMERIC,
  PRIMARY KEY("id")
);
```

`dim_lote` es la granularidad más fina del DW: cada fila es una subdivisión física de un campo. La columna `activo` implementa el patrón de **baja lógica** propio de los Datawarehouses: nunca se elimina una fila con historial, sino que se la desactiva. `tipo_suelo_id` es FK a `dim_tipo_suelo`, descomponiendo en 3FN un atributo que antes estaba como string libre.

`fact_produccion` es la tabla de hechos central. Almacena una fila por lote × cultivo × período de cosecha con las métricas del negocio.

### ETL — Rol en la creación

El ETL no ejecuta DDL (eso lo hacen las migraciones SQL). Su rol en el proceso de *creación de datos* es **poblar `dim_clima`**, la única tabla que no se semilla con datos estáticos sino que se alimenta en tiempo real desde los sensores IoT.

La secuencia es:

```
sensor IoT (campo) ──▶ MongoDB Atlas ──▶ extract_sensor_readings()
                                                  │
                                         transform_readings()
                                         [filtra + agrega por lote × mes]
                                                  │
                                         load_to_dim_clima()
                                         [DELETE + INSERT idempotente]
                                                  │
                                              dim_clima  ◀── nueva fila creada
```

Cada vez que el pipeline corre, crea (o actualiza) registros en `dim_clima` para los lotes activos del período procesado.

---

## 4.b — Eliminación

En un Datawarehouse la eliminación física se evita deliberadamente: borrar una fila destruye el historial que es la razón de ser del DW. En su lugar se usa **baja lógica**.

### Baja lógica (recomendada en DW)

```sql
-- Marca un lote como inactivo sin borrar su historial de producción
UPDATE dim_lote
SET    activo     = FALSE,
       updated_at = NOW()
WHERE  lote_id = 11;
```

El lote queda fuera de todos los procesos futuros (el ETL excluye `activo = FALSE` en `fetch_lotes_activos()`), pero sus registros en `fact_produccion` y `dim_clima` siguen disponibles para análisis histórico.

### Eliminación física (solo corrección de errores ETL)

Cuando el ETL carga un dato incorrecto y hay que revertirlo, la eliminación física es válida. Se deben respetar las dependencias de FK eliminando en orden inverso:

```sql
-- Primero los hijos, luego el padre
DELETE FROM fact_produccion WHERE lote_id = 11;
DELETE FROM dim_clima       WHERE lote_id = 11;
DELETE FROM dim_lote        WHERE lote_id = 11;
```

### ETL — Eliminación para idempotencia

El loader implementa un DELETE interno como parte de su estrategia idempotente. Antes de cada inserción borra las filas de `dim_clima` para las combinaciones `(lote_id, tiempo_id)` que va a cargar, garantizando que no existan duplicados si el pipeline se ejecuta más de una vez sobre el mismo período.

---

## 4.c — Inserción

### SQL

```sql
-- Inserción simple: agrega tres tipos de maquinaria
INSERT INTO "dim_tipo_maquinaria" ("tipo_maquinaria_id", "nombre")
VALUES (1, 'Cosechadora'), (2, 'Sembradora'), (3, 'Pulverizadora');

-- Inserción con UPSERT: si el lote ya existe, actualiza sus atributos
INSERT INTO "dim_lote" ("lote_id", "campo_id", "nombre", "superficie_ha", "activo")
VALUES (15, 2, 'Lote Sur', 120.5, TRUE)
ON CONFLICT ("lote_id")
DO UPDATE SET
  "superficie_ha" = EXCLUDED."superficie_ha",
  "activo"        = EXCLUDED."activo";
```

El patrón `ON CONFLICT ... DO UPDATE` (UPSERT) es fundamental en los Datawarehouses: permite ejecutar el mismo script de carga varias veces sin duplicar datos. Si `lote_id = 15` ya existe, la instrucción actualiza solo los campos indicados; si no existe, los inserta.

### ETL — Inserción en `dim_clima`

El ETL replica exactamente este patrón UPSERT al cargar `dim_clima`. La función `load_to_dim_clima()` inserta una fila por cada combinación `(lote_id, tiempo_id)` procesada:

```
MongoDB          →    transform_readings()    →    load_to_dim_clima()
8.450 lecturas        25 filas agregadas            25 filas en dim_clima
(25 lotes × 7 días)  (1 por lote × mes)            (INSERT con ID explícito)
```

Los campos que se insertan en `dim_clima` son:

| Campo | Origen |
|-------|--------|
| `lote_id` | De cada documento de sensor en MongoDB |
| `tiempo_id` | Resuelto via `fetch_tiempo_map()` consultando `dim_tiempo` |
| `temp_promedio` | Promedio mensual de lecturas `TEMPERATURA` |
| `temp_max` / `temp_min` | Máximo/mínimo mensual de temperatura |
| `humedad_promedio` | Promedio mensual de lecturas `HUMEDAD_SUELO` |
| `precipitacion_mm` | Derivado de humedad (dato sintético) |

---

## 4.d — Actualización

### SQL

```sql
-- Actualización directa: corrige el precio de venta tras un ajuste de mercado
UPDATE fact_produccion
SET    previo_venta_tn_prom = 362.50
WHERE  tiempo_id IN (
           SELECT tiempo_id FROM dim_tiempo
           WHERE  fecha BETWEEN '2024-07-01' AND '2025-06-30'
       )
AND    id_cultivo = (
           SELECT id_cultivo FROM dim_cultivo
           WHERE  cultivo = 'Soja DM 4612 RR'
       );
```

En el DW, los UPDATE ocurren cuando el ETL detecta que un valor previamente cargado era incorrecto: el precio de venta que liquida la cooperativa puede diferir del estimado inicial, o una lectura de sensor puede haber sido corregida.

### ETL — Actualización mediante UPSERT

El ETL no ejecuta `UPDATE` directo. En su lugar implementa el patrón **DELETE + INSERT** (semánticamente equivalente a un UPSERT), que garantiza **idempotencia**: ejecutar el pipeline dos veces sobre el mismo período produce el mismo resultado que ejecutarlo una vez.

```python
# Paso 1 — elimina las filas del período que se va a recargar
client.table("dim_clima")
      .delete()
      .in_("lote_id",   lote_ids)
      .in_("tiempo_id", tiempo_ids)
      .execute()

# Paso 2 — inserta los valores actualizados
client.table("dim_clima").insert(records).execute()
```

Este patrón es equivalente al SQL:

```sql
INSERT INTO dim_clima (clima_id, lote_id, tiempo_id, temp_promedio, humedad_promedio, ...)
VALUES (...)
ON CONFLICT (lote_id, tiempo_id)
DO UPDATE SET
    temp_promedio    = EXCLUDED.temp_promedio,
    humedad_promedio = EXCLUDED.humedad_promedio,
    ...;
```

Cuando el ETL corre nuevamente sobre un período ya procesado (por ejemplo, para incorporar lecturas de sensores que llegaron tarde), el DELETE previo elimina los valores viejos y el INSERT carga los recalculados con los datos completos. El historial en `fact_produccion` no se toca porque esa tabla se alimenta por separado.

---

## 4.e — Búsquedas

### Búsqueda por 1 clave

Búsqueda por clave primaria simple. Usa el índice de PK → acceso en O(log n).

```sql
-- Ejemplo A: un lote específico por su lote_id
SELECT
    l.lote_id,
    l.nombre,
    l.superficie_ha,
    ts.nombre        AS tipo_suelo,
    ca.nombre        AS campo,
    pr.cuit          AS propietario_cuit
FROM  dim_lote        l
JOIN  dim_campo       ca ON ca.campo_id        = l.campo_id
JOIN  dim_propietario pr ON pr.propietario_id  = ca.propietario_id
JOIN  dim_tipo_suelo  ts ON ts.tipo_suelo_id   = l.tipo_suelo_id
WHERE l.lote_id = 1;
```

```sql
-- Ejemplo B: un hecho de producción por su id
SELECT
    f.id,
    f.rendimiento_kg_ha,
    f.superficie_cosechada_ha,
    f.previo_venta_tn_prom,
    t.fecha,
    l.nombre   AS lote,
    c.cultivo
FROM  fact_produccion f
JOIN  dim_tiempo  t ON t.tiempo_id  = f.tiempo_id
JOIN  dim_lote    l ON l.lote_id    = f.lote_id
JOIN  dim_cultivo c ON c.id_cultivo = f.id_cultivo
WHERE f.id = 1;
```

### Búsqueda por 2 claves

Búsqueda que combina dos columnas como criterio de filtro. Utiliza el índice compuesto `idx_fact_lote_tiempo`.

```sql
-- Producción de un lote en una campaña específica
-- Clave 1: lote_id  |  Clave 2: rango de fechas (campaña 2024/25)
SELECT
    l.nombre                                       AS lote,
    ts.nombre                                      AS tipo_suelo,
    t.fecha,
    c.cultivo,
    f.rendimiento_kg_ha,
    f.superficie_cosechada_ha,
    ROUND((f.rendimiento_kg_ha *
           f.superficie_cosechada_ha / 1000)::numeric, 1) AS produccion_tn,
    f.previo_venta_tn_prom,
    f.costo_total
FROM  fact_produccion f
JOIN  dim_lote        l  ON l.lote_id        = f.lote_id
JOIN  dim_tipo_suelo  ts ON ts.tipo_suelo_id = l.tipo_suelo_id
JOIN  dim_tiempo      t  ON t.tiempo_id      = f.tiempo_id
JOIN  dim_cultivo     c  ON c.id_cultivo     = f.id_cultivo
WHERE l.lote_id = 1                                    -- clave 1: lote
AND   t.fecha BETWEEN '2024-07-01' AND '2025-06-30'    -- clave 2: campaña
ORDER BY c.cultivo;
```

```sql
-- Clima de un lote en un mes específico
-- Clave 1: lote_id  |  Clave 2: tiempo_id
SELECT
    l.nombre        AS lote,
    t.fecha,
    cl.temp_promedio,
    cl.temp_max,
    cl.temp_min,
    cl.humedad_promedio,
    cl.precipitacion_mm
FROM  dim_clima  cl
JOIN  dim_lote    l ON l.lote_id   = cl.lote_id
JOIN  dim_tiempo  t ON t.tiempo_id = cl.tiempo_id
WHERE cl.lote_id   = 1
AND   cl.tiempo_id = (SELECT tiempo_id FROM dim_tiempo WHERE fecha = '2025-06-01');
```

---

## Mejoras propuestas al SQL

> **Nota:** las siguientes observaciones no implican cambios en el código — se mencionan a efectos documentales.

1. **Inconsistencia en el nombre de columna de `fact_produccion`:** el DDL proporcionado define la columna como `"cultivo_id"`, pero la FK referencia a `dim_cultivo` cuya PK se llama `"id_cultivo"`. Para mantener consistencia con el esquema real del DW —donde la clave foránea se nombra igual que la PK de la tabla referenciada— sería preferible usar `"id_cultivo"` también en `fact_produccion`.

2. **`campo_id = 2` en el INSERT de `dim_lote`:** el ejemplo inserta un lote con `campo_id = 2` asumiendo que ese campo ya existe en `dim_lote`. En un entorno de producción este valor debería validarse o resolverse dinámicamente (por ejemplo, buscando el `campo_id` por nombre), para evitar errores de FK si el ID difiere al aplicar el script en otra instancia.

3. **Ausencia de FK explícitas en el DDL mostrado:** las sentencias `CREATE TABLE` no incluyen las cláusulas `FOREIGN KEY`. En el esquema completo del proyecto estas constraints se aplican en migraciones separadas (patrón `ALTER TABLE ... ADD FOREIGN KEY`), lo que es válido, pero incluirlas en el DDL inicial haría la definición más autocontenida.
