-- Migración 004: Creación de dim_propietario
-- Hoja de propietarios. CUIT único, datos de contacto.

CREATE TABLE IF NOT EXISTS dim_propietario (
    id           SERIAL       PRIMARY KEY,
    razon_social VARCHAR(200) NOT NULL,
    cuit         VARCHAR(13)  NOT NULL UNIQUE,
    email        VARCHAR(200),
    telefono     VARCHAR(30),
    created_at   TIMESTAMP    DEFAULT NOW(),
    updated_at   TIMESTAMP    DEFAULT NOW()
);
COMMENT ON TABLE dim_propietario IS
  'Hoja propietarios. 3FN: datos del dueño no se repiten en cada campo.';
