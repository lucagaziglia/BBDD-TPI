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
    id          SERIAL       PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL UNIQUE,
    codigo_iso  VARCHAR(10)
);
COMMENT ON TABLE dim_provincia IS
  'Hoja geográfica. 3FN: nombre_provincia no se repite en dim_campo.';

-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_tipo_cultivo (
    id            SERIAL       PRIMARY KEY,
    nombre        VARCHAR(100) NOT NULL UNIQUE,
    especie       VARCHAR(200),
    clasificacion VARCHAR(50)
);
COMMENT ON TABLE dim_tipo_cultivo IS
  'Hoja cultivo. 3FN: clasificacion no se repite en cada variedad.';

-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_tipo_maquinaria (
    id          SERIAL       PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL UNIQUE,
    categoria   VARCHAR(50),
    descripcion TEXT
);
COMMENT ON TABLE dim_tipo_maquinaria IS
  'Hoja maquinaria. 3FN: categoria no se repite en cada equipo.';

-- ────────────────────────────────────────────────────────────

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

-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_tiempo (
    id         SERIAL      PRIMARY KEY,
    fecha      DATE        NOT NULL UNIQUE,
    dia        INT         NOT NULL,
    semana     INT         NOT NULL,
    mes        INT         NOT NULL,
    trimestre  INT         NOT NULL,
    anio       INT         NOT NULL,
    nombre_mes VARCHAR(20) NOT NULL,
    campania   VARCHAR(10) NOT NULL,
    es_feriado BOOLEAN     DEFAULT FALSE
);
COMMENT ON TABLE dim_tiempo IS
  'Jerarquía temporal: día → semana → mes → trimestre → año → campaña agrícola.';

CREATE INDEX IF NOT EXISTS idx_tiempo_fecha    ON dim_tiempo(fecha);
CREATE INDEX IF NOT EXISTS idx_tiempo_campania ON dim_tiempo(campania);
