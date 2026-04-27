-- ============================================================
-- SEED 08 — Dimensión temporal (dim_tiempo)
-- Genera fechas con generate_series para las campañas 2022/2023,
-- 2023/2024 y 2024/2025 (julio a junio del año siguiente).
-- ============================================================

INSERT INTO dim_tiempo (
    fecha, dia, semana, mes, trimestre, anio,
    nombre_mes, campania, es_feriado
)
SELECT
    d::DATE                                         AS fecha,
    EXTRACT(DAY   FROM d)::INT                      AS dia,
    EXTRACT(WEEK  FROM d)::INT                      AS semana,
    EXTRACT(MONTH FROM d)::INT                      AS mes,
    EXTRACT(QUARTER FROM d)::INT                    AS trimestre,
    EXTRACT(YEAR  FROM d)::INT                      AS anio,
    TO_CHAR(d, 'TMMonth')                           AS nombre_mes,
    CASE
        WHEN EXTRACT(MONTH FROM d) >= 7
        THEN EXTRACT(YEAR FROM d)::TEXT || '/' || (EXTRACT(YEAR FROM d)+1)::TEXT
        ELSE (EXTRACT(YEAR FROM d)-1)::TEXT || '/' || EXTRACT(YEAR FROM d)::TEXT
    END                                             AS campania,
    FALSE                                           AS es_feriado
FROM generate_series(
    '2022-07-01'::DATE,
    '2025-06-30'::DATE,
    '1 day'::INTERVAL
) AS g(d)
ON CONFLICT (fecha) DO NOTHING;
