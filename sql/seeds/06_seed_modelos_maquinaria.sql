-- ============================================================
-- SEED 06 — Modelos de maquinaria (dim_modelo_maquinaria) — 9 modelos
-- Depende de: 03_seed_tipos.sql
-- ============================================================

INSERT INTO dim_modelo_maquinaria (tipo_maquinaria_id, marca_maquinaria_id, nombre_modelo)
SELECT t.tipo_maquinaria_id, m.marca_maquinaria_id, v.modelo
FROM (VALUES
  ('Sembradora',    'Agrometal',   'Monumental 3000'),
  ('Sembradora',    'Apache',      'Soja 18'),
  ('Cosechadora',   'John Deere',  'S680'),
  ('Cosechadora',   'New Holland', 'CR9090'),
  ('Cosechadora',   'Case IH',     '7250 AFS'),
  ('Pulverizadora', 'Metalfor',    'Puelche 4200'),
  ('Pulverizadora', 'Jacto',       'Jacto 3030'),
  ('Tractor',       'John Deere',  '7215R'),
  ('Tractor',       'Case IH',     'Puma 185')
) AS v(tipo_nombre, marca_nombre, modelo)
JOIN dim_tipo_maquinaria  t ON t.nombre           = v.tipo_nombre
JOIN dim_marca_maquinaria m ON m.marca_maquinaria = v.marca_nombre
WHERE NOT EXISTS (
    SELECT 1 FROM dim_modelo_maquinaria mm
    WHERE mm.tipo_maquinaria_id  = t.tipo_maquinaria_id
      AND mm.marca_maquinaria_id = m.marca_maquinaria_id
      AND mm.nombre_modelo       = v.modelo
);
