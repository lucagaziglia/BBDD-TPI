-- ============================================================
-- OPERACIÓN: Búsqueda por 2 claves (Ítem 4.5 de la consigna)
-- ============================================================
-- Búsqueda que combina dos columnas como criterio de filtro.
-- Usa el índice compuesto idx_fact_lote_tiempo → eficiente.
-- ============================================================

-- Ejemplo A: Producción de un lote específico en una campaña específica
-- Dos claves: lote_id + campaña (via dim_tiempo)
SELECT
    l.nombre                                   AS lote,
    l.tipo_suelo,
    t.campania,
    ct.nombre                                  AS cultivo,
    f.rendimiento_kg_ha,
    f.superficie_cosechada_ha,
    ROUND((f.rendimiento_kg_ha *
           f.superficie_cosechada_ha / 1000
    )::numeric, 1)                             AS produccion_tn,
    f.precio_venta_tn,
    f.costo_total
FROM  fact_produccion f
JOIN  dim_lote        l  ON l.id  = f.lote_id
JOIN  dim_tiempo      t  ON t.id  = f.tiempo_id
JOIN  dim_cultivo     cv ON cv.id = f.cultivo_id
JOIN  dim_tipo_cultivo ct ON ct.id = cv.tipo_cultivo_id
WHERE l.id        = 1          -- clave 1: lote específico
AND   t.campania  = '2024/2025' -- clave 2: campaña específica
ORDER BY ct.nombre;

-- Ejemplo B: Clima de una localidad en un mes específico
-- Dos claves: localidad_id + fecha
SELECT
    lo.nombre        AS localidad,
    cl.fecha,
    cl.temp_promedio,
    cl.temp_max,
    cl.temp_min,
    cl.humedad_promedio,
    cl.precipitacion_mm
FROM  dim_clima    cl
JOIN  dim_localidad lo ON lo.id = cl.localidad_id
WHERE cl.localidad_id = 1
AND   cl.fecha        = '2024-04-01';

-- Ver el plan de ejecución (confirma uso del índice compuesto)
EXPLAIN ANALYZE
SELECT * FROM fact_produccion
WHERE lote_id = 1
AND   tiempo_id IN (SELECT id FROM dim_tiempo WHERE campania = '2024/2025');
