-- Migración 010: Creación de dim_lote (principal)
-- Granularidad más fina. Depende de dim_campo.
-- activo: columna para baja lógica — en un DW no se eliminan filas físicamente.
-- El ETL excluye lotes inactivos de futuros procesos de carga.

CREATE TABLE IF NOT EXISTS dim_lote (
    id              SERIAL       PRIMARY KEY,
    campo_id        INT          NOT NULL,
    nombre          VARCHAR(100) NOT NULL,
    superficie_ha   FLOAT        NOT NULL,
    tipo_suelo      VARCHAR(50),
    coordenadas_wkt TEXT,
    activo          BOOLEAN      DEFAULT TRUE,
    created_at      TIMESTAMP    DEFAULT NOW(),
    updated_at      TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT fk_lote_campo
        FOREIGN KEY (campo_id) REFERENCES dim_campo(id)
);
COMMENT ON TABLE dim_lote IS
  'Granularidad más fina del DW. activo=FALSE = baja lógica sin perder historial.';
