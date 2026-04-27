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
