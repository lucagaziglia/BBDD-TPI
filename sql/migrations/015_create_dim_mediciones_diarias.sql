CREATE TABLE dim_mediciones_diarias (
    id SERIAL PRIMARY KEY,
    lote_id INTEGER REFERENCES dim_lote(lote_id),
    fecha DATE,
    mes INTEGER,
    temp_prom NUMERIC,
    temp_max NUMERIC,
    temp_min NUMERIC,
    humedad_prom NUMERIC,
    precipitacion_mm NUMERIC,
    m3_agua_consumida NUMERIC
);