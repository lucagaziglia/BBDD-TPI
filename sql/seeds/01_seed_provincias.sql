-- ============================================================
-- SEED 01 — Provincias (dim_provincia)
-- Buenos Aires, Santa Fe, Córdoba
-- ============================================================

INSERT INTO dim_provincia (nombre, codigo_iso) VALUES
  ('Buenos Aires', 'AR-B'),
  ('Santa Fe',     'AR-S'),
  ('Córdoba',      'AR-X')
ON CONFLICT (nombre) DO NOTHING;
