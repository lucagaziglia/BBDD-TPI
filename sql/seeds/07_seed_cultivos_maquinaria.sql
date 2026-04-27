-- ============================================================
-- SEED 07 — Cultivos (dim_cultivo) y Maquinaria (dim_maquinaria)
-- 6 variedades + 9 equipos
-- Depende de: 02_seed_tipos.sql
-- ============================================================

-- Variedades de cultivo
INSERT INTO dim_cultivo (tipo_cultivo_id, variedad, ciclo, densidad_siembra)
SELECT t.id, v.variedad, v.ciclo, v.densidad
FROM (VALUES
  ('Soja',  'DM 4612 RR',    'Largo',   280000),
  ('Soja',  'NS 4009 IPRO',  'Medio',   260000),
  ('Maíz',  'DK 7210 VT3P',  'Largo',    75000),
  ('Maíz',  'P1780 YHR',     'Medio',    80000),
  ('Trigo', 'Klein Proteo',  'Largo',   140000),
  ('Trigo', 'ACA 315',       'Corto',   160000)
) AS v(tipo_nombre, variedad, ciclo, densidad)
JOIN dim_tipo_cultivo t ON t.nombre = v.tipo_nombre
ON CONFLICT DO NOTHING;

-- Equipos de maquinaria
INSERT INTO dim_maquinaria (tipo_maquinaria_id, modelo, marca, anio_fabricacion, numero_serie, estado)
SELECT t.id, v.modelo, v.marca, v.anio, v.serie, 'Operativo'
FROM (VALUES
  ('Sembradora',    'Monumental 3000', 'Agrometal', 2019, 'AGR-SEM-001', NULL),
  ('Sembradora',    'Soja 18',         'Apache',    2021, 'APC-SEM-002', NULL),
  ('Cosechadora',   'S680',            'John Deere',2020, 'JD-COS-001',  NULL),
  ('Cosechadora',   'CR9090',          'New Holland',2018,'NH-COS-002',  NULL),
  ('Cosechadora',   '7250 AFS',        'Case IH',   2022, 'CI-COS-003',  NULL),
  ('Pulverizadora', 'Puelche 4200',    'Metalfor',  2020, 'MF-PUL-001',  NULL),
  ('Pulverizadora', 'Jacto 3030',      'Jacto',     2021, 'JA-PUL-002',  NULL),
  ('Tractor',       '7215R',           'John Deere',2019, 'JD-TRA-001',  NULL),
  ('Tractor',       'Puma 185',        'Case IH',   2021, 'CI-TRA-002',  NULL)
) AS v(tipo_nombre, modelo, marca, anio, serie, estado)
JOIN dim_tipo_maquinaria t ON t.nombre = v.tipo_nombre
ON CONFLICT (numero_serie) DO NOTHING;
