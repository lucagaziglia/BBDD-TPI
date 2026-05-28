-- Migración 005: Creación de dim_tipo_maquinaria
-- Hoja de maquinaria. Tipos: Sembradora, Cosechadora, Pulverizadora, etc.

CREATE TABLE IF NOT EXISTS dim_tipo_maquinaria (
    tipo_maquinaria_id SERIAL       PRIMARY KEY,
    nombre             VARCHAR(255) NOT NULL UNIQUE
);
COMMENT ON TABLE dim_tipo_maquinaria IS
  'Hoja maquinaria. Tipos: Sembradora, Cosechadora, Pulverizadora, etc.';
