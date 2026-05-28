-- Migración 013: Creación de dim_maquinaria (principal)
-- Depende de dim_modelo_maquinaria y dim_estado_maquinaria.

CREATE TABLE IF NOT EXISTS dim_maquinaria (
    maquinaria_id        SERIAL    PRIMARY KEY,
    "año_fabricacion"    INTEGER,
    modelo_maquinaria_id INTEGER   NOT NULL,
    estado_maquinaria_id INTEGER   NOT NULL,
    created_at           TIMESTAMP DEFAULT NOW(),
    updated_at           TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_maquinaria_modelo
        FOREIGN KEY (modelo_maquinaria_id) REFERENCES dim_modelo_maquinaria(modelo_maquinaria_id),
    CONSTRAINT fk_maquinaria_estado
        FOREIGN KEY (estado_maquinaria_id) REFERENCES dim_estado_maquinaria(estado_maquinaria_id)
);
COMMENT ON TABLE dim_maquinaria IS
  'Equipos individuales. 3FN: tipo y marca heredados via dim_modelo_maquinaria.';
