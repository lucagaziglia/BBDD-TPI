-- Migración 005: Creación de dim_tiempo
-- Jerarquía temporal con campaña agrícola (julio→junio).

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
