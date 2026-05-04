-- Migración 007: Creación de dim_estado_maquinaria
-- Hoja de maquinaria. Estados: Operativo, En reparación, Fuera de servicio.

CREATE TABLE IF NOT EXISTS dim_estado_maquinaria (
    estado_maquinaria_id SERIAL       PRIMARY KEY,
    estado               VARCHAR(255) NOT NULL UNIQUE
);
COMMENT ON TABLE dim_estado_maquinaria IS
  'Hoja maquinaria. 3FN: estados centralizados (Operativo, En reparación, etc).';
