-- Migración 011: Creación de dim_clima (principal)
-- Depende de dim_localidad (FK).
-- DISEÑO 3FN: usa localidad_id (no lote_id). El clima es un fenómeno
-- geográfico de zona — si usáramos lote_id existirían dos caminos al
-- mismo lote desde fact_produccion, violando FNBC.
-- JOIN correcto: fact → dim_lote → dim_campo → dim_localidad → dim_clima
-- humedad_promedio: agregado por el ETL desde MongoDB sensor_readings.

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
  '3FN: clima por localidad. ETL: MongoDB → pandas → UPSERT aquí.';

CREATE INDEX IF NOT EXISTS idx_clima_localidad_fecha
    ON dim_clima(localidad_id, fecha);
