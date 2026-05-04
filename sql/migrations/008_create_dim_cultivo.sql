-- Migración 008: Creación de dim_cultivo
-- Hoja de cultivos. Variedades comerciales (Soja DM 4612, Trigo ACA 315, etc).

CREATE TABLE IF NOT EXISTS dim_cultivo (
    id_cultivo SERIAL      PRIMARY KEY,
    cultivo    VARCHAR(50) NOT NULL UNIQUE
);
COMMENT ON TABLE dim_cultivo IS
  'Hoja cultivo. Variedades comerciales (Soja DM 4612, Trigo ACA 315, etc).';
