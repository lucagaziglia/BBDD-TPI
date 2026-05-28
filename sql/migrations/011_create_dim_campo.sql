-- Migración 011: Creación de dim_campo (principal)
-- Depende de dim_propietario y dim_localidad.

CREATE TABLE IF NOT EXISTS dim_campo (
    campo_id       SERIAL       PRIMARY KEY,
    propietario_id INTEGER      NOT NULL,
    localidad_id   INTEGER      NOT NULL,
    nombre         VARCHAR(100) NOT NULL,
    activo         BOOLEAN      DEFAULT TRUE,
    CONSTRAINT fk_campo_propietario
        FOREIGN KEY (propietario_id) REFERENCES dim_propietario(propietario_id),
    CONSTRAINT fk_campo_localidad
        FOREIGN KEY (localidad_id)   REFERENCES dim_localidad(id)
);
COMMENT ON TABLE dim_campo IS
  'Nodo intermedio snowflake: conecta propietario y localidad. activo=baja lógica.';
