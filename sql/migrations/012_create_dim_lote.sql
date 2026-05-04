-- Migración 012: Creación de dim_lote (principal)
-- Granularidad más fina. Depende de dim_campo y dim_tipo_suelo.
-- activo: columna para baja lógica — en un DW no se eliminan filas físicamente.
-- El ETL excluye lotes inactivos de futuros procesos de carga.

CREATE TABLE IF NOT EXISTS dim_lote (
    lote_id       SERIAL         PRIMARY KEY,
    campo_id      INTEGER        NOT NULL,
    nombre        VARCHAR(50)    NOT NULL,
    superficie_ha DECIMAL(10,2)  NOT NULL,
    tipo_suelo_id INTEGER        NOT NULL,
    coordenadas   VARCHAR(255),
    activo        BOOLEAN        DEFAULT TRUE,
    created_at    TIMESTAMP      DEFAULT NOW(),
    updated_at    TIMESTAMP      DEFAULT NOW(),
    CONSTRAINT fk_lote_campo
        FOREIGN KEY (campo_id)      REFERENCES dim_campo(campo_id),
    CONSTRAINT fk_lote_tipo_suelo
        FOREIGN KEY (tipo_suelo_id) REFERENCES dim_tipo_suelo(tipo_suelo_id)
);
COMMENT ON TABLE dim_lote IS
  'Granularidad más fina del DW. activo=FALSE = baja lógica sin perder historial.';
