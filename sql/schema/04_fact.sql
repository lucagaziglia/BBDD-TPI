-- ============================================================
-- SCHEMA 04 — Tabla de hechos central
-- Ejecutar ÚLTIMO, después de todos los schemas anteriores
-- Granularidad: 1 fila por lote × cultivo × tiempo
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_produccion (
    id                      SERIAL         PRIMARY KEY,
    maquinaria_id           INTEGER        NOT NULL,
    id_cultivo              INTEGER        NOT NULL,
    lote_id                 INTEGER        NOT NULL,
    tiempo_id               INTEGER        NOT NULL,
    rendimiento_kg_ha       NUMERIC        NOT NULL,
    superficie_cosechada_ha NUMERIC        NOT NULL,
    costo_total             DECIMAL(10,2)  NOT NULL,
    -- previo_venta_tn_prom: precio promedio de venta por tonelada.
    -- Se actualiza vía ETL cuando la cooperativa liquida la cosecha.
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


-- ============================================================
-- VERIFICACIÓN: ejecutar para confirmar las 15 tablas creadas
-- y el conteo de columnas + FK por tabla.
-- ============================================================
-- SELECT
--     t.table_name                          AS tabla,
--     COUNT(DISTINCT c.column_name)         AS columnas,
--     COUNT(DISTINCT tc.constraint_name)    AS fks
-- FROM information_schema.tables t
-- LEFT JOIN information_schema.columns c
--     ON c.table_name = t.table_name AND c.table_schema = 'public'
-- LEFT JOIN information_schema.table_constraints tc
--     ON tc.table_name = t.table_name
--     AND tc.table_schema = 'public'
--     AND tc.constraint_type = 'FOREIGN KEY'
-- WHERE t.table_schema = 'public'
-- GROUP BY t.table_name
-- ORDER BY t.table_name;
