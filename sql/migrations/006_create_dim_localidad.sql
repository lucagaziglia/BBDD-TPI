-- Migración 006: Creación de dim_localidad (intermedia)
-- Depende de dim_provincia (FK).

CREATE TABLE IF NOT EXISTS dim_localidad (
    id           SERIAL       PRIMARY KEY,
    provincia_id INT          NOT NULL,
    nombre       VARCHAR(150) NOT NULL,
    latitud      FLOAT,
    longitud     FLOAT,
    CONSTRAINT fk_localidad_provincia
        FOREIGN KEY (provincia_id) REFERENCES dim_provincia(id)
);
COMMENT ON TABLE dim_localidad IS
  'Intermedia geográfica. 3FN: nombre_provincia no se repite acá.';
