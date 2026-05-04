-- ============================================================
-- SEED 09 — Maquinaria (dim_maquinaria) — 9 equipos
-- Depende de: 06_seed_modelos_maquinaria.sql, 03_seed_tipos.sql
-- ============================================================

INSERT INTO dim_maquinaria ("año_fabricacion", modelo_maquinaria_id, estado_maquinaria_id)
SELECT v.anio, mm.modelo_maquinaria_id, em.estado_maquinaria_id
FROM (VALUES
  ('Monumental 3000', 2019, 'Operativo'),
  ('Soja 18',         2021, 'Operativo'),
  ('S680',            2020, 'Operativo'),
  ('CR9090',          2018, 'En reparación'),
  ('7250 AFS',        2022, 'Operativo'),
  ('Puelche 4200',    2020, 'Operativo'),
  ('Jacto 3030',      2021, 'Operativo'),
  ('7215R',           2019, 'Operativo'),
  ('Puma 185',        2021, 'Operativo')
) AS v(modelo_nombre, anio, estado_nombre)
JOIN dim_modelo_maquinaria mm ON mm.nombre_modelo = v.modelo_nombre
JOIN dim_estado_maquinaria em ON em.estado        = v.estado_nombre;
