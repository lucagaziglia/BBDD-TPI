-- Migración 003: Creación de dim_tiempo
-- Jerarquía temporal: día → semana → mes → trimestre → año.

CREATE TABLE IF NOT EXISTS dim_tiempo (
    tiempo_id SERIAL  PRIMARY KEY,
    fecha     DATE    NOT NULL UNIQUE,
    dia       INTEGER NOT NULL,
    semana    INTEGER NOT NULL,
    mes       INTEGER NOT NULL,
    trimestre INTEGER NOT NULL,
    "año"     INTEGER NOT NULL
);
COMMENT ON TABLE dim_tiempo IS
  'Jerarquía temporal: día → semana → mes → trimestre → año.';

CREATE INDEX IF NOT EXISTS idx_tiempo_fecha ON dim_tiempo(fecha);
CREATE INDEX IF NOT EXISTS idx_tiempo_anio  ON dim_tiempo("año");
