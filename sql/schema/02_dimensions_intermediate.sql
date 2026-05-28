-- ============================================================
-- SCHEMA 02 — Dimensiones intermedias (FK a hojas)
-- Ejecutar DESPUÉS de 01_dimensions_leaf.sql
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_localidad (
    id           SERIAL      PRIMARY KEY,
    provincia_id INTEGER     NOT NULL,
    nombre       VARCHAR(50) NOT NULL,
    CONSTRAINT fk_localidad_provincia
        FOREIGN KEY (provincia_id) REFERENCES dim_provincia(id)
);
COMMENT ON TABLE dim_localidad IS
  'Intermedia geográfica. 3FN: nombre_provincia no se repite acá.';

-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_modelo_maquinaria (
    modelo_maquinaria_id SERIAL       PRIMARY KEY,
    tipo_maquinaria_id   INTEGER      NOT NULL,
    marca_maquinaria_id  INTEGER      NOT NULL,
    nombre_modelo        VARCHAR(255) NOT NULL,
    CONSTRAINT fk_modelo_tipo
        FOREIGN KEY (tipo_maquinaria_id) REFERENCES dim_tipo_maquinaria(tipo_maquinaria_id),
    CONSTRAINT fk_modelo_marca
        FOREIGN KEY (marca_maquinaria_id) REFERENCES dim_marca_maquinaria(marca_maquinaria_id)
);
COMMENT ON TABLE dim_modelo_maquinaria IS
  'Modelos. 3FN: combina tipo+marca, evita repetir esos atributos en dim_maquinaria.';
