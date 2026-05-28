-- ============================================================
-- SEED 08 — Lotes (dim_lote) — 25 registros con tipo_suelo via FK
-- Depende de: 07_seed_campos.sql, 03_seed_tipos.sql
-- ============================================================

INSERT INTO dim_lote (campo_id, nombre, superficie_ha, tipo_suelo_id, activo)
SELECT c.campo_id, v.nombre, v.superficie_ha, ts.tipo_suelo_id, TRUE
FROM (VALUES
  -- Campo Norte (Pergamino, propietario 1)
  ('Campo Norte',    'Lote 1 - Arroyo',      120.0, 'Franco limoso'),
  ('Campo Norte',    'Lote 2 - Laguna',       95.0, 'Franco arcilloso'),
  ('Campo Norte',    'Lote 3 - La Rinconada', 80.0, 'Arenoso'),
  -- Campo Sur (Junín, propietario 1)
  ('Campo Sur',      'Lote 1 - Norte',       110.0, 'Franco limoso'),
  ('Campo Sur',      'Lote 2 - Sur',          95.0, 'Arcilloso'),
  -- El Tajamar (Pergamino, propietario 2)
  ('El Tajamar',     'Lote A',               145.0, 'Franco limoso'),
  ('El Tajamar',     'Lote B',               140.0, 'Franco arcilloso'),
  ('El Tajamar',     'Lote C',               145.0, 'Arcilloso'),
  -- La Barrancosa (Rosario, propietario 3)
  ('La Barrancosa',  'Lote 1',               200.0, 'Vertisol'),
  ('La Barrancosa',  'Lote 2',               190.0, 'Vertisol'),
  ('La Barrancosa',  'Lote 3',               195.0, 'Arenoso'),
  ('La Barrancosa',  'Lote 4',               185.0, 'Franco limoso'),
  -- Loma Verde (Venado Tuerto, propietario 3)
  ('Loma Verde',     'Lote 1 - Este',        170.0, 'Franco limoso'),
  ('Loma Verde',     'Lote 2 - Oeste',       170.0, 'Franco arcilloso'),
  ('Loma Verde',     'Lote 3 - Centro',      170.0, 'Arcilloso'),
  -- San Cayetano (Nueve de Julio, propietario 4)
  ('San Cayetano',   'Lote 1',               190.0, 'Franco limoso'),
  ('San Cayetano',   'Lote 2',               185.0, 'Arenoso'),
  ('San Cayetano',   'Lote 3',               190.0, 'Franco limoso'),
  ('San Cayetano',   'Lote 4',               195.0, 'Arcilloso'),
  -- La Esperanza (Córdoba Capital, propietario 5)
  ('La Esperanza',   'Lote Norte',           170.0, 'Franco limoso'),
  ('La Esperanza',   'Lote Sur',             170.0, 'Arcilloso'),
  -- El Retiro (Río Cuarto, propietario 6)
  ('El Retiro',      'Lote 1',               275.0, 'Franco limoso'),
  ('El Retiro',      'Lote 2',               275.0, 'Vertisol'),
  -- Las Vertientes (Venado Tuerto, propietario 6)
  ('Las Vertientes', 'Lote 1 - Principal',   295.0, 'Franco arcilloso'),
  ('Las Vertientes', 'Lote 2 - Secundario',  295.0, 'Franco limoso')
) AS v(campo_nombre, nombre, superficie_ha, tipo_suelo_nombre)
JOIN dim_campo      c  ON c.nombre  = v.campo_nombre
JOIN dim_tipo_suelo ts ON ts.nombre = v.tipo_suelo_nombre
WHERE NOT EXISTS (
    SELECT 1 FROM dim_lote l
    WHERE l.campo_id = c.campo_id
      AND l.nombre   = v.nombre
);
