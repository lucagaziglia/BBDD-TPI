-- Migración 014: Creación de dim_clima (principal)
-- Depende de dim_lote y dim_tiempo.
-- humedad_promedio: agregado por el ETL desde MongoDB sensor_readings.

CREATE TABLE IF NOT EXISTS dim_clima (
    clima_id         SERIAL   PRIMARY KEY,
    lote_id          INTEGER  NOT NULL,
    temp_promedio    NUMERIC,
    temp_max         NUMERIC,
    temp_min         NUMERIC,
    tiempo_id        INTEGER  NOT NULL,
    humedad_promedio NUMERIC,
    precipitacion_mm NUMERIC,
    CONSTRAINT fk_clima_lote
        FOREIGN KEY (lote_id)   REFERENCES dim_lote(lote_id),
    CONSTRAINT fk_clima_tiempo
        FOREIGN KEY (tiempo_id) REFERENCES dim_tiempo(tiempo_id),
    CONSTRAINT uq_clima_lote_tiempo
        UNIQUE (lote_id, tiempo_id)
);
COMMENT ON TABLE dim_clima IS
  'Clima por lote × tiempo. ETL: MongoDB → pandas → UPSERT aquí.';

CREATE INDEX IF NOT EXISTS idx_clima_lote_tiempo
    ON dim_clima(lote_id, tiempo_id);
