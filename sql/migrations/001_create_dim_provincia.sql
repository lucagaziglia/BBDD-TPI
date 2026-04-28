-- Migración 001: Creación de dim_provincia
-- Hoja geográfica del snowflake. No tiene FK a otras tablas.

CREATE TABLE IF NOT EXISTS dim_provincia (
    id          SERIAL       PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL UNIQUE,
    codigo_iso  VARCHAR(10)
);
COMMENT ON TABLE dim_provincia IS
  'Hoja geográfica. 3FN: nombre_provincia no se repite en dim_campo.';
