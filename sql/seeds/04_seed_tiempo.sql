-- ============================================================
-- SEED 04 — Dimensión temporal (dim_tiempo)
-- 36 registros: primer día de cada mes desde Jul 2022 a Jun 2025.
-- Cubre las 3 campañas: 2022/23, 2023/24 (sequía), 2024/25.
-- ============================================================

INSERT INTO dim_tiempo (fecha, dia, semana, mes, trimestre, "año")
SELECT
    d::DATE                              AS fecha,
    EXTRACT(DAY     FROM d)::INT         AS dia,
    EXTRACT(WEEK    FROM d)::INT         AS semana,
    EXTRACT(MONTH   FROM d)::INT         AS mes,
    EXTRACT(QUARTER FROM d)::INT         AS trimestre,
    EXTRACT(YEAR    FROM d)::INT         AS "año"
FROM generate_series(
    '2022-07-01'::DATE,
    '2025-06-01'::DATE,
    '1 month'::INTERVAL
) AS g(d)
ON CONFLICT (fecha) DO NOTHING;
