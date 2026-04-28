-- Migración 003: Creación de dim_tipo_maquinaria
-- Hoja de maquinaria. Centraliza categoría/descripción por tipo.

CREATE TABLE IF NOT EXISTS dim_tipo_maquinaria (
    id          SERIAL       PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL UNIQUE,
    categoria   VARCHAR(50),
    descripcion TEXT
);
COMMENT ON TABLE dim_tipo_maquinaria IS
  'Hoja maquinaria. 3FN: categoria no se repite en cada equipo.';
