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
    -- activo: columna para baja lógica en operaciones de eliminación
    -- En un DW no se eliminan filas físicamente — se marca activo=FALSE
    -- El ETL excluye lotes inactivos de futuros procesos de carga
    activo          BOOLEAN      DEFAULT TRUE,
    created_at      TIMESTAMP    DEFAULT NOW(),
    updated_at      TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT fk_lote_campo
        FOREIGN KEY (campo_id) REFERENCES dim_campo(id)
);
COMMENT ON TABLE dim_lote IS
  'Granularidad más fina del DW. activo=FALSE = baja lógica sin perder historial.';

-- ────────────────────────────────────────────────────────────

-- CORRECCIÓN 3FN (migración 012):
-- dim_clima usa localidad_id en lugar de lote_id.
-- JUSTIFICACIÓN: el clima es un fenómeno geográfico de zona,
-- no de lote individual. Con lote_id existían dos caminos al
-- mismo lote desde fact_produccion, violando FNBC:
--   fact.lote_id → dim_lote
--   fact.clima_id → dim_clima.lote_id → dim_lote  ← redundante
-- Con localidad_id ese problema desaparece.
-- JOIN correcto: fact → dim_lote → dim_campo → dim_localidad → dim_clima
CREATE TABLE IF NOT EXISTS dim_clima (
    id                SERIAL    PRIMARY KEY,
    localidad_id      INT       NOT NULL,
    fecha             DATE      NOT NULL,
    temp_promedio     FLOAT,
    temp_max          FLOAT,
    temp_min          FLOAT,
    -- humedad_promedio: agregado por el ETL desde MongoDB sensor_readings
    humedad_promedio  FLOAT,
    precipitacion_mm  FLOAT,
    created_at        TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_clima_localidad
        FOREIGN KEY (localidad_id) REFERENCES dim_localidad(id),
    CONSTRAINT uq_clima_localidad_fecha
        UNIQUE (localidad_id, fecha)
);
COMMENT ON TABLE dim_clima IS
  '3FN: clima por localidad. ETL: MongoDB → pandas → UPSERT aquí.';

CREATE INDEX IF NOT EXISTS idx_clima_localidad_fecha
    ON dim_clima(localidad_id, fecha);
