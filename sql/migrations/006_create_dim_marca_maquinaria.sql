-- Migración 006: Creación de dim_marca_maquinaria
-- Hoja de maquinaria. Marcas: John Deere, Case IH, New Holland, etc.

CREATE TABLE IF NOT EXISTS dim_marca_maquinaria (
    marca_maquinaria_id SERIAL       PRIMARY KEY,
    marca_maquinaria    VARCHAR(255) NOT NULL UNIQUE
);
COMMENT ON TABLE dim_marca_maquinaria IS
  'Hoja maquinaria. Marcas: John Deere, Case IH, New Holland, etc.';
