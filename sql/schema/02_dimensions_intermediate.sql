-- ============================================================
-- SCHEMA 02 — Dimensiones intermedias (FK a hojas)
-- Ejecutar DESPUÉS de 01_dimensions_leaf.sql
-- ============================================================

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

CREATE TABLE IF NOT EXISTS dim_campo (
    id                  SERIAL       PRIMARY KEY,
    propietario_id      INT          NOT NULL,
    localidad_id        INT          NOT NULL,
    nombre              VARCHAR(200) NOT NULL,
    superficie_total_ha FLOAT        NOT NULL,
    created_at          TIMESTAMP    DEFAULT NOW(),
    updated_at          TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT fk_campo_propietario
        FOREIGN KEY (propietario_id) REFERENCES dim_propietario(id),
    CONSTRAINT fk_campo_localidad
        FOREIGN KEY (localidad_id)   REFERENCES dim_localidad(id)
);
COMMENT ON TABLE dim_campo IS
  'Nodo intermedio snowflake: conecta propietario y localidad sin repetir ninguno.';

CREATE TABLE IF NOT EXISTS dim_cultivo (
    id               SERIAL       PRIMARY KEY,
    tipo_cultivo_id  INT          NOT NULL,
    variedad         VARCHAR(100) NOT NULL,
    ciclo            VARCHAR(30),
    densidad_siembra INT,
    created_at       TIMESTAMP    DEFAULT NOW(),
    updated_at       TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT fk_cultivo_tipo
        FOREIGN KEY (tipo_cultivo_id) REFERENCES dim_tipo_cultivo(id)
);
COMMENT ON TABLE dim_cultivo IS
  'Variedades de cultivo. 3FN: clasificacion/especie heredadas de dim_tipo_cultivo.';

CREATE TABLE IF NOT EXISTS dim_maquinaria (
    id                 SERIAL       PRIMARY KEY,
    tipo_maquinaria_id INT          NOT NULL,
    modelo             VARCHAR(100) NOT NULL,
    marca              VARCHAR(100) NOT NULL,
    anio_fabricacion   INT,
    numero_serie       VARCHAR(50)  UNIQUE,
    estado             VARCHAR(30),
    created_at         TIMESTAMP    DEFAULT NOW(),
    updated_at         TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT fk_maquinaria_tipo
        FOREIGN KEY (tipo_maquinaria_id) REFERENCES dim_tipo_maquinaria(id)
);
COMMENT ON TABLE dim_maquinaria IS
  'Equipos individuales. 3FN: categoria heredada de dim_tipo_maquinaria.';
