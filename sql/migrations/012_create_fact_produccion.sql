-- Migración 013: Creación de fact_produccion + índices de soporte
-- Tabla de hechos central. FK a las 5 dimensiones.
-- Granularidad: 1 fila por lote × cultivo × campaña.
-- precio_venta_tn: se actualiza vía ETL cuando la cooperativa liquida.

CREATE TABLE IF NOT EXISTS fact_produccion (
    id                      SERIAL PRIMARY KEY,
    lote_id                 INT    NOT NULL,
    cultivo_id              INT    NOT NULL,
    tiempo_id               INT    NOT NULL,
    maquinaria_id           INT    NOT NULL,
    clima_id                INT    NOT NULL,
    rendimiento_kg_ha       FLOAT  NOT NULL,
    superficie_cosechada_ha FLOAT  NOT NULL,
    costo_total             FLOAT  NOT NULL,
    precio_venta_tn         FLOAT,
    horas_maquinaria        INT,
    created_at              TIMESTAMP DEFAULT NOW(),
    updated_at              TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_fact_lote
        FOREIGN KEY (lote_id)       REFERENCES dim_lote(id),
    CONSTRAINT fk_fact_cultivo
        FOREIGN KEY (cultivo_id)    REFERENCES dim_cultivo(id),
    CONSTRAINT fk_fact_tiempo
        FOREIGN KEY (tiempo_id)     REFERENCES dim_tiempo(id),
    CONSTRAINT fk_fact_maquinaria
        FOREIGN KEY (maquinaria_id) REFERENCES dim_maquinaria(id),
    CONSTRAINT fk_fact_clima
        FOREIGN KEY (clima_id)      REFERENCES dim_clima(id)
);
COMMENT ON TABLE fact_produccion IS
  'Tabla de hechos. Granularidad: 1 fila por lote × cultivo × campaña.';

CREATE INDEX IF NOT EXISTS idx_fact_lote_tiempo
    ON fact_produccion(lote_id, tiempo_id);
CREATE INDEX IF NOT EXISTS idx_fact_cultivo_tiempo
    ON fact_produccion(cultivo_id, tiempo_id);
CREATE INDEX IF NOT EXISTS idx_fact_rendimiento
    ON fact_produccion(rendimiento_kg_ha);
