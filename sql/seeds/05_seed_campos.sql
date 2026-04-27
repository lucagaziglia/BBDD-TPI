-- ============================================================
-- SEED 05 — Campos (dim_campo) — 9 registros
-- Depende de: 03_seed_propietarios.sql, 04_seed_localidades.sql
-- ============================================================

INSERT INTO dim_campo (propietario_id, localidad_id, nombre, superficie_total_ha)
SELECT p.id, l.id, v.nombre, v.superficie_ha
FROM (VALUES
  ('Agropecuaria Del Valle S.A.',  'Pergamino',       'Campo Norte',        850.0),
  ('Agropecuaria Del Valle S.A.',  'Junín',           'Campo Sur',          620.0),
  ('Los Alamos Agro S.R.L.',       'Pergamino',       'El Tajamar',         430.0),
  ('Establecimiento El Pampero',   'Rosario',         'La Barrancosa',      970.0),
  ('Establecimiento El Pampero',   'Venado Tuerto',   'Loma Verde',         510.0),
  ('Granos del Sur S.A.',          'Nueve de Julio',  'San Cayetano',       760.0),
  ('Familia Gómez e Hijos S.H.',   'Córdoba Capital', 'La Esperanza',       340.0),
  ('AgroPampa Inversiones S.A.',   'Río Cuarto',      'El Retiro',         1100.0),
  ('AgroPampa Inversiones S.A.',   'Venado Tuerto',   'Las Vertientes',     890.0)
) AS v(propietario_rs, localidad_nombre, nombre, superficie_ha)
JOIN dim_propietario p ON p.razon_social = v.propietario_rs
JOIN dim_localidad   l ON l.nombre       = v.localidad_nombre
ON CONFLICT DO NOTHING;
