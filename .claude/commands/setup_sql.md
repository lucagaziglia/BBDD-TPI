# /setup_sql — Estructurar la carpeta sql/ completa del repo

Organizá toda la carpeta sql/ del proyecto BBDD-TPI con la estructura correcta.
Creá todos los archivos separados según su rol. No preguntes nada, ejecutá todo.

El estado actual es: existe un archivo `der_completo_desde_cero.sql` o similar
con todo mezclado. Hay que separarlo en archivos individuales con la estructura
que se describe abajo.

---

## Estructura objetivo

```
sql/
├── schema/
│   ├── 01_dimensions_leaf.sql
│   ├── 02_dimensions_intermediate.sql
│   ├── 03_dimensions_main.sql
│   └── 04_fact.sql
├── seeds/
│   ├── 01_seed_provincias.sql
│   ├── 02_seed_tipos.sql
│   ├── 03_seed_propietarios.sql
│   ├── 04_seed_localidades.sql
│   ├── 05_seed_campos.sql
│   ├── 06_seed_lotes.sql
│   ├── 07_seed_cultivos_maquinaria.sql
│   ├── 08_seed_tiempo.sql
│   └── 09_seed_fact.sql
├── queries/
│   ├── mining/
│   │   ├── segmentacion_lotes.sql
│   │   └── prediccion_rendimiento.sql
│   └── bi/
│       ├── rendimiento_por_campania.sql
│       └── produccion_por_propietario.sql
└── operations/
    ├── delete_ejemplo.sql
    ├── update_ejemplo.sql
    ├── busqueda_1_clave.sql
    └── busqueda_2_claves.sql
```

---

## Archivo: `sql/schema/01_dimensions_leaf.sql`

```sql
-- ============================================================
-- SCHEMA 01 — Dimensiones hoja (sin FK a otras tablas del DW)
-- AgroPampa S.A. — Datawarehouse Snowflake en 3FN
-- UNSAM · Bases de Datos · TP Final 2025
-- ============================================================
-- Estas tablas no tienen FK a otras tablas del DW.
-- Son el nivel base de la jerarquía snowflake.
-- Deben crearse PRIMERO antes que cualquier otra tabla.
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_provincia (
    id          SERIAL       PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL UNIQUE,
    codigo_iso  VARCHAR(10)
);
COMMENT ON TABLE dim_provincia IS
  'Hoja geográfica. 3FN: nombre_provincia no se repite en dim_campo.';

CREATE TABLE IF NOT EXISTS dim_tipo_cultivo (
    id            SERIAL       PRIMARY KEY,
    nombre        VARCHAR(100) NOT NULL UNIQUE,
    especie       VARCHAR(200),
    clasificacion VARCHAR(50)
);
COMMENT ON TABLE dim_tipo_cultivo IS
  'Hoja cultivo. 3FN: clasificacion no se repite en cada variedad.';

CREATE TABLE IF NOT EXISTS dim_tipo_maquinaria (
    id          SERIAL       PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL UNIQUE,
    categoria   VARCHAR(50),
    descripcion TEXT
);
COMMENT ON TABLE dim_tipo_maquinaria IS
  'Hoja maquinaria. 3FN: categoria no se repite en cada equipo.';

CREATE TABLE IF NOT EXISTS dim_propietario (
    id           SERIAL       PRIMARY KEY,
    razon_social VARCHAR(200) NOT NULL,
    cuit         VARCHAR(13)  NOT NULL UNIQUE,
    email        VARCHAR(200),
    telefono     VARCHAR(30),
    created_at   TIMESTAMP    DEFAULT NOW(),
    updated_at   TIMESTAMP    DEFAULT NOW()
);
COMMENT ON TABLE dim_propietario IS
  'Hoja propietarios. 3FN: datos del dueño no se repiten en cada campo.';

CREATE TABLE IF NOT EXISTS dim_tiempo (
    id         SERIAL      PRIMARY KEY,
    fecha      DATE        NOT NULL UNIQUE,
    dia        INT         NOT NULL,
    semana     INT         NOT NULL,
    mes        INT         NOT NULL,
    trimestre  INT         NOT NULL,
    anio       INT         NOT NULL,
    nombre_mes VARCHAR(20) NOT NULL,
    campania   VARCHAR(10) NOT NULL,
    es_feriado BOOLEAN     DEFAULT FALSE
);
COMMENT ON TABLE dim_tiempo IS
  'Jerarquía temporal: día → semana → mes → trimestre → año → campaña agrícola.';

CREATE INDEX IF NOT EXISTS idx_tiempo_fecha    ON dim_tiempo(fecha);
CREATE INDEX IF NOT EXISTS idx_tiempo_campania ON dim_tiempo(campania);
```

---

## Archivo: `sql/schema/02_dimensions_intermediate.sql`

```sql
-- ============================================================
-- SCHEMA 02 — Dimensiones intermedias (FK a hojas)
-- Ejecutar DESPUÉS de 01_dimensions_leaf.sql
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_localidad (
    id           SERIAL       PRIMARY KEY,
    provincia_id INT          NOT NULL,
    nombre       VARCHAR(150) NOT NULL,
    latitud      FLOAT,
    longitud     FLOAT,
    CONSTRAINT fk_localidad_provincia
        FOREIGN KEY (provincia_id) REFERENCES dim_provincia(id)
);
COMMENT ON TABLE dim_localidad IS
  'Intermedia geográfica. 3FN: nombre_provincia no se repite acá.';

CREATE TABLE IF NOT EXISTS dim_campo (
    id                  SERIAL       PRIMARY KEY,
    propietario_id      INT          NOT NULL,
    localidad_id        INT          NOT NULL,
    nombre              VARCHAR(200) NOT NULL,
    superficie_total_ha FLOAT        NOT NULL,
    created_at          TIMESTAMP    DEFAULT NOW(),
    updated_at          TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT fk_campo_propietario
        FOREIGN KEY (propietario_id) REFERENCES dim_propietario(id),
    CONSTRAINT fk_campo_localidad
        FOREIGN KEY (localidad_id)   REFERENCES dim_localidad(id)
);
COMMENT ON TABLE dim_campo IS
  'Nodo intermedio snowflake: conecta propietario y localidad sin repetir ninguno.';

CREATE TABLE IF NOT EXISTS dim_cultivo (
    id               SERIAL       PRIMARY KEY,
    tipo_cultivo_id  INT          NOT NULL,
    variedad         VARCHAR(100) NOT NULL,
    ciclo            VARCHAR(30),
    densidad_siembra INT,
    created_at       TIMESTAMP    DEFAULT NOW(),
    updated_at       TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT fk_cultivo_tipo
        FOREIGN KEY (tipo_cultivo_id) REFERENCES dim_tipo_cultivo(id)
);
COMMENT ON TABLE dim_cultivo IS
  'Variedades de cultivo. 3FN: clasificacion/especie heredadas de dim_tipo_cultivo.';

CREATE TABLE IF NOT EXISTS dim_maquinaria (
    id                 SERIAL       PRIMARY KEY,
    tipo_maquinaria_id INT          NOT NULL,
    modelo             VARCHAR(100) NOT NULL,
    marca              VARCHAR(100) NOT NULL,
    anio_fabricacion   INT,
    numero_serie       VARCHAR(50)  UNIQUE,
    estado             VARCHAR(30),
    created_at         TIMESTAMP    DEFAULT NOW(),
    updated_at         TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT fk_maquinaria_tipo
        FOREIGN KEY (tipo_maquinaria_id) REFERENCES dim_tipo_maquinaria(id)
);
COMMENT ON TABLE dim_maquinaria IS
  'Equipos individuales. 3FN: categoria heredada de dim_tipo_maquinaria.';
```

---

## Archivo: `sql/schema/03_dimensions_main.sql`

```sql
-- ============================================================
-- SCHEMA 03 — Dimensiones principales (FK a intermedias)
-- Ejecutar DESPUÉS de 02_dimensions_intermediate.sql
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_lote (
    id              SERIAL       PRIMARY KEY,
    campo_id        INT          NOT NULL,
    nombre          VARCHAR(100) NOT NULL,
    superficie_ha   FLOAT        NOT NULL,
    tipo_suelo      VARCHAR(50),
    coordenadas_wkt TEXT,
    activo          BOOLEAN      DEFAULT TRUE,
    created_at      TIMESTAMP    DEFAULT NOW(),
    updated_at      TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT fk_lote_campo
        FOREIGN KEY (campo_id) REFERENCES dim_campo(id)
);
COMMENT ON TABLE dim_lote IS
  'Granularidad más fina del DW. Hereda propietario y localidad vía dim_campo.';

-- ============================================================
-- dim_clima: usa localidad_id (NO lote_id)
-- JUSTIFICACIÓN 3FN: el clima es un fenómeno geográfico de zona.
-- Si usáramos lote_id, fact_produccion tendría dos caminos al
-- mismo lote (fact.lote_id y fact.clima_id→dim_clima.lote_id),
-- violando FNBC. Con localidad_id ese camino no existe.
-- ============================================================
CREATE TABLE IF NOT EXISTS dim_clima (
    id                SERIAL    PRIMARY KEY,
    localidad_id      INT       NOT NULL,
    fecha             DATE      NOT NULL,
    temp_promedio     FLOAT,
    temp_max          FLOAT,
    temp_min          FLOAT,
    humedad_promedio  FLOAT,
    precipitacion_mm  FLOAT,
    created_at        TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_clima_localidad
        FOREIGN KEY (localidad_id) REFERENCES dim_localidad(id),
    CONSTRAINT uq_clima_localidad_fecha
        UNIQUE (localidad_id, fecha)
);
COMMENT ON TABLE dim_clima IS
  '3FN: clima por localidad, no por lote. Alimentada por ETL desde MongoDB.
   JOIN: fact → dim_lote → dim_campo → dim_localidad → dim_clima.';

CREATE INDEX IF NOT EXISTS idx_clima_localidad_fecha
    ON dim_clima(localidad_id, fecha);
```

---

## Archivo: `sql/schema/04_fact.sql`

```sql
-- ============================================================
-- SCHEMA 04 — Tabla de hechos central
-- Ejecutar ÚLTIMO, después de todos los schemas anteriores
-- Granularidad: 1 fila por lote × cultivo × campaña
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_produccion (
    id                      SERIAL PRIMARY KEY,
    lote_id                 INT    NOT NULL,
    cultivo_id              INT    NOT NULL,
    tiempo_id               INT    NOT NULL,
    maquinaria_id           INT    NOT NULL,
    clima_id                INT    NOT NULL,
    rendimiento_kg_ha       FLOAT  NOT NULL,
    superficie_cosechada_ha FLOAT  NOT NULL,
    costo_total             FLOAT  NOT NULL,
    precio_venta_tn         FLOAT,
    horas_maquinaria        INT,
    created_at              TIMESTAMP DEFAULT NOW(),
    updated_at              TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_fact_lote
        FOREIGN KEY (lote_id)       REFERENCES dim_lote(id),
    CONSTRAINT fk_fact_cultivo
        FOREIGN KEY (cultivo_id)    REFERENCES dim_cultivo(id),
    CONSTRAINT fk_fact_tiempo
        FOREIGN KEY (tiempo_id)     REFERENCES dim_tiempo(id),
    CONSTRAINT fk_fact_maquinaria
        FOREIGN KEY (maquinaria_id) REFERENCES dim_maquinaria(id),
    CONSTRAINT fk_fact_clima
        FOREIGN KEY (clima_id)      REFERENCES dim_clima(id)
);
COMMENT ON TABLE fact_produccion IS
  'Tabla de hechos central. Granularidad: 1 fila por lote × cultivo × campaña.';

CREATE INDEX IF NOT EXISTS idx_fact_lote_tiempo
    ON fact_produccion(lote_id, tiempo_id);
CREATE INDEX IF NOT EXISTS idx_fact_cultivo_tiempo
    ON fact_produccion(cultivo_id, tiempo_id);
CREATE INDEX IF NOT EXISTS idx_fact_rendimiento
    ON fact_produccion(rendimiento_kg_ha);
```

---

## Archivos de seeds: `sql/seeds/`

Creá un archivo por cada migración de seed que ya existe en Supabase.
El contenido de cada archivo es el INSERT correspondiente.
No hace falta que sean ejecutables ahora — son documentación del estado inicial.

Creá los siguientes archivos vacíos con un comentario de cabecera:

- `sql/seeds/01_seed_provincias.sql` → Buenos Aires, Santa Fe, Córdoba
- `sql/seeds/02_seed_tipos.sql` → tipos cultivo y maquinaria
- `sql/seeds/03_seed_propietarios.sql` → 6 propietarios
- `sql/seeds/04_seed_localidades.sql` → 7 localidades
- `sql/seeds/05_seed_campos.sql` → 9 campos
- `sql/seeds/06_seed_lotes.sql` → 25 lotes con tipo_suelo
- `sql/seeds/07_seed_cultivos_maquinaria.sql` → 6 variedades, 9 equipos
- `sql/seeds/08_seed_tiempo.sql` → dim_tiempo con generate_series
- `sql/seeds/09_seed_fact.sql` → 150 filas fact_produccion con Box-Muller

Para el contenido de cada seed, extraerlo de los comentarios del CLAUDE.md
o de las migraciones ya aplicadas en Supabase.

---

## Archivos de operaciones: `sql/operations/`

Creá estos 4 archivos con el contenido indicado:

### `sql/operations/delete_ejemplo.sql`
```sql
-- ============================================================
-- OPERACIÓN: Eliminación (Ítem 4.2 de la consigna)
-- ============================================================
-- ETL Context: En un DW raramente se eliminan filas — se hace
-- "baja lógica" marcando el registro como inactivo.
-- Solo se elimina físicamente en casos de error de carga o
-- datos duplicados detectados en el proceso ETL.
-- ============================================================

-- Ejemplo A: Baja lógica (recomendado en DW)
-- Marca un lote como inactivo sin borrar el historial
UPDATE dim_lote
SET    activo = FALSE,
       updated_at = NOW()
WHERE  id = 11;  -- Lote 3 - La Rinconada (suelo arenoso, bajo rendimiento)

-- Verificar el resultado
SELECT id, nombre, tipo_suelo, activo
FROM   dim_lote
WHERE  id = 11;

-- Ejemplo B: Eliminación física (solo para corregir errores ETL)
-- PRECAUCIÓN: eliminar de fact_produccion primero por integridad referencial
-- DELETE FROM fact_produccion WHERE lote_id = 11;
-- DELETE FROM dim_lote        WHERE id      = 11;
```

### `sql/operations/update_ejemplo.sql`
```sql
-- ============================================================
-- OPERACIÓN: Actualización (Ítem 4.4 de la consigna)
-- ============================================================
-- ETL Context: El UPDATE en un DW ocurre cuando el ETL detecta
-- que un valor procesado anteriormente era incorrecto (precio
-- de mercado corregido, lectura de sensor fuera de rango, etc.)
-- Se usa ON CONFLICT DO UPDATE (UPSERT) para garantizar
-- idempotencia: si el pipeline corre dos veces, no duplica datos.
-- ============================================================

-- Ejemplo A: Actualizar precio de venta tras corrección de mercado
UPDATE fact_produccion
SET    precio_venta_tn = 362.50,
       updated_at      = NOW()
WHERE  tiempo_id  = (SELECT id FROM dim_tiempo WHERE campania = '2024/2025' LIMIT 1)
AND    cultivo_id = (SELECT id FROM dim_cultivo LIMIT 1);

-- Verificar el resultado
SELECT f.id, t.campania, c.variedad, f.precio_venta_tn, f.updated_at
FROM   fact_produccion f
JOIN   dim_tiempo  t ON t.id = f.tiempo_id
JOIN   dim_cultivo c ON c.id = f.cultivo_id
WHERE  t.campania = '2024/2025'
LIMIT  5;

-- Ejemplo B: UPSERT en dim_clima (patrón del ETL)
-- Esto es exactamente lo que hace el loader del pipeline cada día
INSERT INTO dim_clima (localidad_id, fecha, temp_promedio, humedad_promedio)
VALUES (1, CURRENT_DATE, 22.5, 65.3)
ON CONFLICT (localidad_id, fecha) DO UPDATE SET
    temp_promedio    = EXCLUDED.temp_promedio,
    humedad_promedio = EXCLUDED.humedad_promedio,
    created_at       = NOW();
```

### `sql/operations/busqueda_1_clave.sql`
```sql
-- ============================================================
-- OPERACIÓN: Búsqueda por 1 clave (Ítem 4.5 de la consigna)
-- ============================================================
-- Búsqueda por clave primaria simple (id).
-- Usa el índice de PK → O(log n), muy eficiente.
-- ============================================================

-- Ejemplo A: Buscar un lote por su id
SELECT
    l.id,
    l.nombre,
    l.superficie_ha,
    l.tipo_suelo,
    ca.nombre AS campo,
    pr.razon_social AS propietario
FROM  dim_lote l
JOIN  dim_campo      ca ON ca.id = l.campo_id
JOIN  dim_propietario pr ON pr.id = ca.propietario_id
WHERE l.id = 1;

-- Ejemplo B: Buscar un hecho de producción por su id
SELECT
    f.id,
    f.rendimiento_kg_ha,
    f.superficie_cosechada_ha,
    f.precio_venta_tn,
    t.campania,
    l.nombre AS lote
FROM  fact_produccion f
JOIN  dim_tiempo t ON t.id = f.tiempo_id
JOIN  dim_lote   l ON l.id = f.lote_id
WHERE f.id = 1;

-- Ver el plan de ejecución (confirma uso de índice)
EXPLAIN ANALYZE
SELECT * FROM fact_produccion WHERE id = 1;
```

### `sql/operations/busqueda_2_claves.sql`
```sql
-- ============================================================
-- OPERACIÓN: Búsqueda por 2 claves (Ítem 4.5 de la consigna)
-- ============================================================
-- Búsqueda que combina dos columnas como criterio de filtro.
-- Usa el índice compuesto idx_fact_lote_tiempo → eficiente.
-- ============================================================

-- Ejemplo A: Producción de un lote específico en una campaña específica
-- Dos claves: lote_id + campaña (via dim_tiempo)
SELECT
    l.nombre                                   AS lote,
    l.tipo_suelo,
    t.campania,
    ct.nombre                                  AS cultivo,
    f.rendimiento_kg_ha,
    f.superficie_cosechada_ha,
    ROUND((f.rendimiento_kg_ha *
           f.superficie_cosechada_ha / 1000
    )::numeric, 1)                             AS produccion_tn,
    f.precio_venta_tn,
    f.costo_total
FROM  fact_produccion f
JOIN  dim_lote        l  ON l.id  = f.lote_id
JOIN  dim_tiempo      t  ON t.id  = f.tiempo_id
JOIN  dim_cultivo     cv ON cv.id = f.cultivo_id
JOIN  dim_tipo_cultivo ct ON ct.id = cv.tipo_cultivo_id
WHERE l.id        = 1          -- clave 1: lote específico
AND   t.campania  = '2024/2025' -- clave 2: campaña específica
ORDER BY ct.nombre;

-- Ejemplo B: Clima de una localidad en un mes específico
-- Dos claves: localidad_id + fecha
SELECT
    lo.nombre        AS localidad,
    cl.fecha,
    cl.temp_promedio,
    cl.temp_max,
    cl.temp_min,
    cl.humedad_promedio,
    cl.precipitacion_mm
FROM  dim_clima    cl
JOIN  dim_localidad lo ON lo.id = cl.localidad_id
WHERE cl.localidad_id = 1
AND   cl.fecha        = '2024-04-01';

-- Ver el plan de ejecución (confirma uso del índice compuesto)
EXPLAIN ANALYZE
SELECT * FROM fact_produccion
WHERE lote_id = 1
AND   tiempo_id IN (SELECT id FROM dim_tiempo WHERE campania = '2024/2025');
```

---

## Archivos de queries: `sql/queries/`

Creá estos archivos vacíos por ahora con solo el comentario de cabecera.
El contenido real se generará con el comando /mining:

### `sql/queries/mining/segmentacion_lotes.sql`
```sql
-- ============================================================
-- MINERÍA: Segmentación dinámica de lotes (Ítem 5.1)
-- Método: NTILE + rankings en SQL puro
-- Variables: rendimiento_kg_ha, coeficiente de variación, tipo_suelo
-- Grupos: alto rendimiento / rendimiento medio / bajo riesgo
-- Contenido completo: ejecutar /mining
-- ============================================================
```

### `sql/queries/mining/prediccion_rendimiento.sql`
```sql
-- ============================================================
-- MINERÍA: Predicción dinámica de rendimiento (Ítem 5.2)
-- Método: Regresión lineal OLS en SQL puro
-- x: humedad_promedio (dim_clima)
-- y: rendimiento_kg_ha (fact_produccion)
-- β₁ = Σ((x-x̄)(y-ȳ)) / Σ((x-x̄)²)
-- β₀ = ȳ - β₁·x̄
-- Contenido completo: ejecutar /mining
-- ============================================================
```

### `sql/queries/bi/rendimiento_por_campania.sql`
```sql
-- ============================================================
-- BI: Evolución de rendimiento por campaña (Dashboard elemento 1)
-- ============================================================
SELECT
    t.campania,
    ct.nombre                              AS cultivo,
    COUNT(*)                               AS lotes,
    ROUND(AVG(f.rendimiento_kg_ha)::numeric, 0) AS rend_promedio_kg_ha,
    ROUND(MIN(f.rendimiento_kg_ha)::numeric, 0) AS rend_min,
    ROUND(MAX(f.rendimiento_kg_ha)::numeric, 0) AS rend_max,
    ROUND(STDDEV(f.rendimiento_kg_ha)::numeric, 0) AS desv_std
FROM   fact_produccion f
JOIN   dim_tiempo       t  ON t.id  = f.tiempo_id
JOIN   dim_cultivo      cv ON cv.id = f.cultivo_id
JOIN   dim_tipo_cultivo ct ON ct.id = cv.tipo_cultivo_id
GROUP  BY t.campania, ct.nombre
ORDER  BY ct.nombre, t.campania;
```

### `sql/queries/bi/produccion_por_propietario.sql`
```sql
-- ============================================================
-- BI: Producción total por propietario (Dashboard elemento 2)
-- ============================================================
SELECT
    pr.razon_social                        AS propietario,
    t.campania,
    COUNT(DISTINCT l.id)                   AS lotes,
    ROUND(AVG(f.rendimiento_kg_ha)::numeric, 0)              AS rend_promedio,
    ROUND(SUM(f.rendimiento_kg_ha *
              f.superficie_cosechada_ha / 1000)::numeric, 1) AS produccion_tn
FROM   fact_produccion f
JOIN   dim_lote         l  ON l.id  = f.lote_id
JOIN   dim_campo        ca ON ca.id = l.campo_id
JOIN   dim_propietario  pr ON pr.id = ca.propietario_id
JOIN   dim_tiempo        t ON t.id  = f.tiempo_id
GROUP  BY pr.razon_social, t.campania
ORDER  BY pr.razon_social, t.campania;
```

---

## Verificación final

Después de crear todos los archivos, corré este comando en la terminal
para confirmar la estructura:

```bash
find sql/ -type f -name "*.sql" | sort
```

Resultado esperado: 17 archivos .sql distribuidos en schema/, seeds/,
operations/ y queries/.

Además, verificá que el README.md mencione la carpeta sql/ y su propósito.
Si no lo menciona, agregá una sección SQL al README explicando el orden
de ejecución de los schemas.
