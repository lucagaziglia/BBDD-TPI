-- ============================================================
-- SEED 05 — Localidades (dim_localidad) — 7 registros
-- Depende de: 01_seed_provincias.sql
-- ============================================================

INSERT INTO dim_localidad (provincia_id, nombre)
SELECT p.id, v.nombre
FROM (VALUES
  ('Buenos Aires', 'Pergamino'),
  ('Buenos Aires', 'Junín'),
  ('Buenos Aires', 'Nueve de Julio'),
  ('Santa Fe',     'Rosario'),
  ('Santa Fe',     'Venado Tuerto'),
  ('Córdoba',      'Córdoba Capital'),
  ('Córdoba',      'Río Cuarto')
) AS v(provincia_nombre, nombre)
JOIN dim_provincia p ON p.nombre = v.provincia_nombre
WHERE NOT EXISTS (
    SELECT 1 FROM dim_localidad l
    WHERE l.provincia_id = p.id AND l.nombre = v.nombre
);
