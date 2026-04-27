-- ============================================================
-- SEED 03 — Propietarios (dim_propietario) — 6 registros
-- ============================================================

INSERT INTO dim_propietario (razon_social, cuit, email, telefono) VALUES
  ('Agropecuaria Del Valle S.A.',  '30-71234567-8', 'info@delvalle.com.ar',    '+54 11 4444-0001'),
  ('Los Alamos Agro S.R.L.',       '30-72345678-9', 'admin@losalamos.com.ar',  '+54 11 4444-0002'),
  ('Establecimiento El Pampero',   '30-73456789-0', 'elpampero@agro.com.ar',   '+54 11 4444-0003'),
  ('Granos del Sur S.A.',          '30-74567890-1', 'contacto@granosdelsur.ar','+54 11 4444-0004'),
  ('Familia Gómez e Hijos S.H.',   '30-75678901-2', 'gomez.campo@gmail.com',   '+54 11 4444-0005'),
  ('AgroPampa Inversiones S.A.',   '30-76789012-3', 'inversiones@agropampa.ar','+54 11 4444-0006')
ON CONFLICT (cuit) DO NOTHING;
