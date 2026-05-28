-- Migración 004: Creación de dim_tipo_suelo
-- Hoja del suelo. Centraliza tipos: Franco, Arcilloso, Arenoso, etc.

CREATE TABLE IF NOT EXISTS dim_tipo_suelo (
    tipo_suelo_id SERIAL       PRIMARY KEY,
    nombre        VARCHAR(255) NOT NULL UNIQUE
);
COMMENT ON TABLE dim_tipo_suelo IS
  'Hoja suelo. 3FN: tipo_suelo deja de repetirse como string en dim_lote.';
