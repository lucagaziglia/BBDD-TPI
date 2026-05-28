-- ============================================================
-- SEED 01 — Provincias (dim_provincia)
-- Buenos Aires, Santa Fe, Córdoba (núcleo de la Pampa húmeda)
-- ============================================================

INSERT INTO dim_provincia (nombre) VALUES
  ('Buenos Aires'),
  ('Santa Fe'),
  ('Córdoba')
ON CONFLICT (nombre) DO NOTHING;
