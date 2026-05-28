-- Migración 001: Creación de dim_provincia
-- Hoja geográfica del snowflake. No tiene FK a otras tablas.

CREATE TABLE IF NOT EXISTS dim_provincia (
    id     SERIAL      PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);
COMMENT ON TABLE dim_provincia IS
  'Hoja geográfica. 3FN: nombre_provincia no se repite en dim_localidad.';
