-- Migración 002: Creación de dim_propietario
-- Hoja de propietarios. CUIT único, datos de contacto, baja lógica via activo.

CREATE TABLE IF NOT EXISTS dim_propietario (
    propietario_id SERIAL       PRIMARY KEY,
    email          VARCHAR(100),
    cuit           VARCHAR(20)  UNIQUE,
    telefono       VARCHAR(255),
    activo         BOOLEAN      DEFAULT TRUE
);
COMMENT ON TABLE dim_propietario IS
  'Hoja propietarios. activo = baja lógica del propietario.';
