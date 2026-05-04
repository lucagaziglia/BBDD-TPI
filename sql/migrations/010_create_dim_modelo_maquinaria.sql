-- Migración 010: Creación de dim_modelo_maquinaria (intermedia)
-- Depende de dim_tipo_maquinaria y dim_marca_maquinaria.
-- Combina tipo + marca para evitar repetir esos atributos en dim_maquinaria.

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
