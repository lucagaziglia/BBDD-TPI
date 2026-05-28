-- ============================================================
-- SEED 07 — Campos (dim_campo) — 9 registros
-- Depende de: 02_seed_propietarios.sql, 05_seed_localidades.sql
-- Identificación de propietario por CUIT (no hay razón social).
-- ============================================================

INSERT INTO dim_campo (propietario_id, localidad_id, nombre, activo)
SELECT p.propietario_id, l.id, v.nombre, TRUE
FROM (VALUES
  ('30-71234567-8', 'Pergamino',       'Campo Norte'),
  ('30-71234567-8', 'Junín',           'Campo Sur'),
  ('30-72345678-9', 'Pergamino',       'El Tajamar'),
  ('30-73456789-0', 'Rosario',         'La Barrancosa'),
  ('30-73456789-0', 'Venado Tuerto',   'Loma Verde'),
  ('30-74567890-1', 'Nueve de Julio',  'San Cayetano'),
  ('30-75678901-2', 'Córdoba Capital', 'La Esperanza'),
  ('30-76789012-3', 'Río Cuarto',      'El Retiro'),
  ('30-76789012-3', 'Venado Tuerto',   'Las Vertientes')
) AS v(propietario_cuit, localidad_nombre, nombre)
JOIN dim_propietario p ON p.cuit   = v.propietario_cuit
JOIN dim_localidad   l ON l.nombre = v.localidad_nombre
WHERE NOT EXISTS (
    SELECT 1 FROM dim_campo c
    WHERE c.propietario_id = p.propietario_id
      AND c.localidad_id   = l.id
      AND c.nombre         = v.nombre
);
