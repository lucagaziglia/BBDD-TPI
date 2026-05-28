-- ============================================================
-- SCHEMA 03 — Dimensiones principales (FK a intermedias)
-- Ejecutar DESPUÉS de 02_dimensions_intermediate.sql
-- ============================================================

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

-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_lote (
    lote_id       SERIAL         PRIMARY KEY,
    campo_id      INTEGER        NOT NULL,
    nombre        VARCHAR(50)    NOT NULL,
    superficie_ha DECIMAL(10,2)  NOT NULL,
    tipo_suelo_id INTEGER        NOT NULL,
    coordenadas   VARCHAR(255),
    -- activo: columna para baja lógica en operaciones de eliminación.
    -- En un DW no se eliminan filas físicamente — se marca activo=FALSE.
    -- El ETL excluye lotes inactivos de futuros procesos de carga.
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

-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_maquinaria (
    maquinaria_id        SERIAL    PRIMARY KEY,
    "año_fabricacion"    INTEGER,
    modelo_maquinaria_id INTEGER   NOT NULL,
    estado_maquinaria_id INTEGER   NOT NULL,
    created_at           TIMESTAMP DEFAULT NOW(),
    updated_at           TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_maquinaria_modelo
        FOREIGN KEY (modelo_maquinaria_id) REFERENCES dim_modelo_maquinaria(modelo_maquinaria_id),
    CONSTRAINT fk_maquinaria_estado
        FOREIGN KEY (estado_maquinaria_id) REFERENCES dim_estado_maquinaria(estado_maquinaria_id)
);
COMMENT ON TABLE dim_maquinaria IS
  'Equipos individuales. 3FN: tipo y marca heredados via dim_modelo_maquinaria.';

-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_clima (
    clima_id         SERIAL   PRIMARY KEY,
    lote_id          INTEGER  NOT NULL,
    temp_promedio    NUMERIC,
    temp_max         NUMERIC,
    temp_min         NUMERIC,
    tiempo_id        INTEGER  NOT NULL,
    -- humedad_promedio: agregado por el ETL desde MongoDB sensor_readings.
    humedad_promedio NUMERIC,
    precipitacion_mm NUMERIC,
    CONSTRAINT fk_clima_lote
        FOREIGN KEY (lote_id)   REFERENCES dim_lote(lote_id),
    CONSTRAINT fk_clima_tiempo
        FOREIGN KEY (tiempo_id) REFERENCES dim_tiempo(tiempo_id),
    CONSTRAINT uq_clima_lote_tiempo
        UNIQUE (lote_id, tiempo_id)
);
COMMENT ON TABLE dim_clima IS
  'Clima por lote × tiempo. ETL: MongoDB → pandas → UPSERT aquí.';

CREATE INDEX IF NOT EXISTS idx_clima_lote_tiempo
    ON dim_clima(lote_id, tiempo_id);
