-- Migración 002: Creación de dim_tipo_cultivo
-- Hoja del cultivo. Centraliza especie y clasificación por tipo.

CREATE TABLE IF NOT EXISTS dim_tipo_cultivo (
    id            SERIAL       PRIMARY KEY,
    nombre        VARCHAR(100) NOT NULL UNIQUE,
    especie       VARCHAR(200),
    clasificacion VARCHAR(50)
);
COMMENT ON TABLE dim_tipo_cultivo IS
  'Hoja cultivo. 3FN: clasificacion no se repite en cada variedad.';
