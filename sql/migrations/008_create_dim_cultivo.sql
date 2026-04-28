-- Migración 008: Creación de dim_cultivo (intermedia)
-- Depende de dim_tipo_cultivo. Variedades comerciales.

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
  'Variedades. 3FN: clasificacion/especie heredadas de dim_tipo_cultivo.';
