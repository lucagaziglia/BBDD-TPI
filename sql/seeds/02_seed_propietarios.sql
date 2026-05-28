-- ============================================================
-- SEED 02 — Propietarios (dim_propietario) — 6 registros
-- Identificados por CUIT (no hay razón social en el nuevo esquema).
-- ============================================================

INSERT INTO dim_propietario (email, cuit, telefono, activo) VALUES
  ('info@delvalle.com.ar',     '30-71234567-8', '+54 11 4444-0001', TRUE),
  ('admin@losalamos.com.ar',   '30-72345678-9', '+54 11 4444-0002', TRUE),
  ('elpampero@agro.com.ar',    '30-73456789-0', '+54 11 4444-0003', TRUE),
  ('contacto@granosdelsur.ar', '30-74567890-1', '+54 11 4444-0004', TRUE),
  ('gomez.campo@gmail.com',    '30-75678901-2', '+54 11 4444-0005', TRUE),
  ('inversiones@agropampa.ar', '30-76789012-3', '+54 11 4444-0006', TRUE)
ON CONFLICT (cuit) DO NOTHING;
