-- ============================================================
-- SCHEMA 01 — Dimensiones hoja (sin FK a otras tablas del DW)
-- AgroPampa S.A. — Datawarehouse Snowflake en 3FN
-- UNSAM · Bases de Datos · TP Final 2025
-- ============================================================
-- Estas tablas no tienen FK a otras tablas del DW.
-- Son el nivel base de la jerarquía snowflake.
-- Deben crearse PRIMERO antes que cualquier otra tabla.
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_provincia (
    id     SERIAL      PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);
COMMENT ON TABLE dim_provincia IS
  'Hoja geográfica. 3FN: nombre_provincia no se repite en dim_localidad.';

-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_propietario (
    propietario_id SERIAL       PRIMARY KEY,
    email          VARCHAR(100),
    cuit           VARCHAR(20)  UNIQUE,
    telefono       VARCHAR(255),
    activo         BOOLEAN      DEFAULT TRUE
);
COMMENT ON TABLE dim_propietario IS
  'Hoja propietarios. activo = baja lógica del propietario.';

-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_tiempo (
    tiempo_id SERIAL  PRIMARY KEY,
    fecha     DATE    NOT NULL UNIQUE,
    dia       INTEGER NOT NULL,
    semana    INTEGER NOT NULL,
    mes       INTEGER NOT NULL,
    trimestre INTEGER NOT NULL,
    "año"     INTEGER NOT NULL
);
COMMENT ON TABLE dim_tiempo IS
  'Jerarquía temporal: día → semana → mes → trimestre → año.';

CREATE INDEX IF NOT EXISTS idx_tiempo_fecha ON dim_tiempo(fecha);
CREATE INDEX IF NOT EXISTS idx_tiempo_anio  ON dim_tiempo("año");

-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_estado_maquinaria (
    estado_maquinaria_id SERIAL       PRIMARY KEY,
    estado               VARCHAR(255) NOT NULL UNIQUE
);
COMMENT ON TABLE dim_estado_maquinaria IS
  'Hoja maquinaria. 3FN: estados centralizados (Operativo, En reparación, etc).';

-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_tipo_suelo (
    tipo_suelo_id SERIAL       PRIMARY KEY,
    nombre        VARCHAR(255) NOT NULL UNIQUE
);
COMMENT ON TABLE dim_tipo_suelo IS
  'Hoja suelo. 3FN: tipo_suelo deja de repetirse como string en dim_lote.';

-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_tipo_maquinaria (
    tipo_maquinaria_id SERIAL       PRIMARY KEY,
    nombre             VARCHAR(255) NOT NULL UNIQUE
);
COMMENT ON TABLE dim_tipo_maquinaria IS
  'Hoja maquinaria. Tipos: Sembradora, Cosechadora, Pulverizadora, etc.';

-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_marca_maquinaria (
    marca_maquinaria_id SERIAL       PRIMARY KEY,
    marca_maquinaria    VARCHAR(255) NOT NULL UNIQUE
);
COMMENT ON TABLE dim_marca_maquinaria IS
  'Hoja maquinaria. Marcas: John Deere, Case IH, New Holland, etc.';

-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_cultivo (
    id_cultivo SERIAL      PRIMARY KEY,
    cultivo    VARCHAR(50) NOT NULL UNIQUE
);
COMMENT ON TABLE dim_cultivo IS
  'Hoja cultivo. Variedades comerciales (Soja DM 4612, Trigo ACA 315, etc).';
