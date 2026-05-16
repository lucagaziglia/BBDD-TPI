-- Generación de mediciones diarias de prueba para la nueva tabla en cascada
INSERT INTO dim_mediciones_diarias (
    lote_id, fecha, mes, temp_prom, temp_max, temp_min, humedad_prom, precipitacion_mm, m3_agua_consumida
)
SELECT 
    l.lote_id,
    d::DATE AS fecha,
    EXTRACT(MONTH FROM d)::INT AS mes,
    ROUND((18 + RANDOM() * 10)::numeric, 2),
    ROUND((28 + RANDOM() * 10)::numeric, 2),
    ROUND((10 + RANDOM() * 10)::numeric, 2),
    ROUND((60 + RANDOM() * 20)::numeric, 2),
    ROUND((RANDOM() * 50)::numeric, 2),
    ROUND((RANDOM() * 100)::numeric, 2)
FROM dim_lote l
CROSS JOIN generate_series('2024-01-01'::DATE, '2024-12-31'::DATE, '1 day'::INTERVAL) AS g(d)
ON CONFLICT (lote_id, fecha) DO NOTHING;