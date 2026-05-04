-- ============================================================
-- OPERACIÓN: Búsqueda por 2 claves (Ítem 4.5 de la consigna)
-- ============================================================
-- Búsqueda que combina dos columnas como criterio de filtro.
-- Usa el índice compuesto idx_fact_lote_tiempo → eficiente.
-- ============================================================

-- Ejemplo A: Producción de un lote específico en una campaña específica
-- Dos claves: lote_id + año (la campaña 2024/25 incluye fechas con año=2024 desde jul
-- y año=2025 hasta jun → filtramos por rango de fechas).
SELECT
    l.nombre                                   AS lote,
    ts.nombre                                  AS tipo_suelo,
    t.fecha,
    c.cultivo,
    f.rendimiento_kg_ha,
    f.superficie_cosechada_ha,
    ROUND((f.rendimiento_kg_ha *
           f.superficie_cosechada_ha / 1000
    )::numeric, 1)                             AS produccion_tn,
    f.previo_venta_tn_prom,
    f.costo_total
FROM  fact_produccion f
JOIN  dim_lote        l  ON l.lote_id      = f.lote_id
JOIN  dim_tipo_suelo  ts ON ts.tipo_suelo_id = l.tipo_suelo_id
JOIN  dim_tiempo      t  ON t.tiempo_id    = f.tiempo_id
JOIN  dim_cultivo     c  ON c.id_cultivo   = f.id_cultivo
WHERE l.lote_id = 1                                       -- clave 1: lote
AND   t.fecha BETWEEN '2024-07-01' AND '2025-06-30'       -- clave 2: campaña 2024/25
ORDER BY c.cultivo;

-- Ejemplo B: Clima de un lote en un mes específico
-- Dos claves: lote_id + tiempo_id
SELECT
    l.nombre        AS lote,
    t.fecha,
    cl.temp_promedio,
    cl.temp_max,
    cl.temp_min,
    cl.humedad_promedio,
    cl.precipitacion_mm
FROM  dim_clima  cl
JOIN  dim_lote    l ON l.lote_id   = cl.lote_id
JOIN  dim_tiempo  t ON t.tiempo_id = cl.tiempo_id
WHERE cl.lote_id   = 1
AND   cl.tiempo_id = (SELECT tiempo_id FROM dim_tiempo WHERE fecha = '2024-04-01');

-- Ver el plan de ejecución (confirma uso del índice compuesto)
EXPLAIN ANALYZE
SELECT * FROM fact_produccion
WHERE lote_id = 1
AND   tiempo_id IN (
    SELECT tiempo_id FROM dim_tiempo
    WHERE fecha BETWEEN '2024-07-01' AND '2025-06-30'
);
