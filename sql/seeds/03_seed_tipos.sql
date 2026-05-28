-- ============================================================
-- SEED 03 — Tipos hoja: suelo, tipo/marca/estado de maquinaria, cultivos
-- ============================================================

-- Tipos de suelo
INSERT INTO dim_tipo_suelo (nombre) VALUES
  ('Franco'),
  ('Franco limoso'),
  ('Franco arcilloso'),
  ('Arcilloso'),
  ('Arenoso'),
  ('Vertisol')
ON CONFLICT (nombre) DO NOTHING;

-- Tipos de maquinaria
INSERT INTO dim_tipo_maquinaria (nombre) VALUES
  ('Sembradora'),
  ('Cosechadora'),
  ('Pulverizadora'),
  ('Tractor')
ON CONFLICT (nombre) DO NOTHING;

-- Marcas de maquinaria
INSERT INTO dim_marca_maquinaria (marca_maquinaria) VALUES
  ('John Deere'),
  ('Case IH'),
  ('New Holland'),
  ('Agrometal'),
  ('Apache'),
  ('Metalfor'),
  ('Jacto')
ON CONFLICT (marca_maquinaria) DO NOTHING;

-- Estados de maquinaria
INSERT INTO dim_estado_maquinaria (estado) VALUES
  ('Operativo'),
  ('En reparación'),
  ('Fuera de servicio')
ON CONFLICT (estado) DO NOTHING;

-- Cultivos (variedades; prefijo Soja/Trigo permite agrupar por tipo en queries)
INSERT INTO dim_cultivo (cultivo) VALUES
  ('Soja DM 4612 RR'),
  ('Soja NS 4009 IPRO'),
  ('Soja Don Mario'),
  ('Trigo Klein Proteo'),
  ('Trigo ACA 315'),
  ('Trigo Buck')
ON CONFLICT (cultivo) DO NOTHING;
