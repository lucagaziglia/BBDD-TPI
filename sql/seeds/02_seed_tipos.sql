-- ============================================================
-- SEED 02 — Tipos de cultivo y tipos de maquinaria
-- ============================================================

INSERT INTO dim_tipo_cultivo (nombre, especie, clasificacion) VALUES
  ('Soja',  'Glycine max',        'Oleaginosa'),
  ('Maíz',  'Zea mays',           'Cereal'),
  ('Trigo', 'Triticum aestivum',  'Cereal')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO dim_tipo_maquinaria (nombre, categoria, descripcion) VALUES
  ('Sembradora',      'Siembra',    'Equipo de siembra directa'),
  ('Cosechadora',     'Cosecha',    'Cosechadora de granos'),
  ('Pulverizadora',   'Fitosanidad','Aplicación de agroquímicos'),
  ('Tractor',         'Tracción',   'Tractor de uso general')
ON CONFLICT (nombre) DO NOTHING;
