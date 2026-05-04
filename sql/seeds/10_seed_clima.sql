-- ============================================================
-- SEED 10 — Clima (dim_clima) — 25 lotes × 36 meses = 900 registros
-- Depende de: 08_seed_lotes.sql, 04_seed_tiempo.sql
-- Genera variabilidad por campaña (2023/24 = sequía -18%) y por lote.
-- ============================================================

INSERT INTO dim_clima (
    lote_id, tiempo_id, temp_promedio, temp_max, temp_min,
    humedad_promedio, precipitacion_mm
)
SELECT
    l.lote_id,
    t.tiempo_id,
    -- Temperatura promedio: variación estacional + ruido
    ROUND((18 + 8 * SIN(2 * PI() * (t.mes - 1) / 12.0)
              + (RANDOM() - 0.5) * 4)::numeric, 2)         AS temp_promedio,
    ROUND((28 + 8 * SIN(2 * PI() * (t.mes - 1) / 12.0)
              + (RANDOM() - 0.5) * 5)::numeric, 2)         AS temp_max,
    ROUND((10 + 8 * SIN(2 * PI() * (t.mes - 1) / 12.0)
              + (RANDOM() - 0.5) * 5)::numeric, 2)         AS temp_min,
    -- Humedad: cae en sequía (campaña 2023/24)
    ROUND((CASE
              WHEN t.fecha BETWEEN '2023-07-01' AND '2024-06-30'
                  THEN 45 + RANDOM() * 15   -- sequía
              ELSE 60 + RANDOM() * 20
           END)::numeric, 2)                               AS humedad_promedio,
    -- Precipitación: cae fuerte en sequía
    ROUND((CASE
              WHEN t.fecha BETWEEN '2023-07-01' AND '2024-06-30'
                  THEN RANDOM() * 60        -- sequía
              ELSE 30 + RANDOM() * 100
           END)::numeric, 2)                               AS precipitacion_mm
FROM dim_lote   l
CROSS JOIN dim_tiempo t
ON CONFLICT (lote_id, tiempo_id) DO NOTHING;
