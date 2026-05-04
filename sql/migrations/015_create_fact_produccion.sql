-- Migración 015: Creación de fact_produccion + índices de soporte
-- Tabla de hechos central. FK a las 4 dimensiones (lote, cultivo, maquinaria, tiempo).
-- Granularidad: 1 fila por lote × cultivo × tiempo (campaña).
-- previo_venta_tn_prom: se actualiza vía ETL cuando la cooperativa liquida.

CREATE TABLE IF NOT EXISTS fact_produccion (
    id                      SERIAL         PRIMARY KEY,
    maquinaria_id           INTEGER        NOT NULL,
    id_cultivo              INTEGER        NOT NULL,
    lote_id                 INTEGER        NOT NULL,
    tiempo_id               INTEGER        NOT NULL,
    rendimiento_kg_ha       NUMERIC        NOT NULL,
    superficie_cosechada_ha NUMERIC        NOT NULL,
    costo_total             DECIMAL(10,2)  NOT NULL,
    previo_venta_tn_prom    NUMERIC,
    CONSTRAINT fk_fact_maquinaria
        FOREIGN KEY (maquinaria_id) REFERENCES dim_maquinaria(maquinaria_id),
    CONSTRAINT fk_fact_cultivo
        FOREIGN KEY (id_cultivo)    REFERENCES dim_cultivo(id_cultivo),
    CONSTRAINT fk_fact_lote
        FOREIGN KEY (lote_id)       REFERENCES dim_lote(lote_id),
    CONSTRAINT fk_fact_tiempo
        FOREIGN KEY (tiempo_id)     REFERENCES dim_tiempo(tiempo_id)
);
COMMENT ON TABLE fact_produccion IS
  'Tabla de hechos. Granularidad: 1 fila por lote × cultivo × tiempo (campaña).';

CREATE INDEX IF NOT EXISTS idx_fact_lote_tiempo
    ON fact_produccion(lote_id, tiempo_id);
CREATE INDEX IF NOT EXISTS idx_fact_cultivo_tiempo
    ON fact_produccion(id_cultivo, tiempo_id);
CREATE INDEX IF NOT EXISTS idx_fact_rendimiento
    ON fact_produccion(rendimiento_kg_ha);
