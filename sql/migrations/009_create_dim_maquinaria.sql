-- Migración 009: Creación de dim_maquinaria (intermedia)
-- Depende de dim_tipo_maquinaria. Equipos individuales (numero_serie único).

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
