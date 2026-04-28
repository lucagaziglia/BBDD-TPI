-- Migración 007: Creación de dim_campo (intermedia)
-- Depende de dim_propietario y dim_localidad.

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
  'Nodo intermedio snowflake: conecta propietario y localidad.';
