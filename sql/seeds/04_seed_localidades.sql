-- ============================================================
-- SEED 04 — Localidades (dim_localidad) — 7 registros
-- Depende de: 01_seed_provincias.sql
-- ============================================================

INSERT INTO dim_localidad (provincia_id, nombre, latitud, longitud)
SELECT p.id, v.nombre, v.latitud, v.longitud
FROM (VALUES
  ('Buenos Aires', 'Pergamino',        -33.8900, -60.5700),
  ('Buenos Aires', 'Junín',            -34.5900, -60.9500),
  ('Buenos Aires', 'Nueve de Julio',   -35.4500, -60.8800),
  ('Santa Fe',     'Rosario',          -32.9468, -60.6393),
  ('Santa Fe',     'Venado Tuerto',    -33.7400, -61.9700),
  ('Córdoba',      'Córdoba Capital',  -31.4167, -64.1833),
  ('Córdoba',      'Río Cuarto',       -33.1306, -64.3497)
) AS v(provincia_nombre, nombre, latitud, longitud)
JOIN dim_provincia p ON p.nombre = v.provincia_nombre
ON CONFLICT DO NOTHING;
