-- ==============================================================================
-- Segmentación Dinámica (NTILE) - Minería de Datos (Ítem 5)
-- ==============================================================================
-- Objetivo: Clasificar los lotes en 3 grupos (terciles) según su rendimiento 
-- histórico promedio. Esto ayuda a segmentar en Lotes Premium, Estándar y Riesgosos.

WITH rendimiento_por_lote AS (
    SELECT 
        l.id AS lote_id,
        c.nombre AS tipo_suelo, -- Asumiendo que el tipo de suelo está en la dimensión de lote/campo
        AVG(f.rendimiento_kg_ha) AS rendimiento_promedio,
        STDDEV(f.rendimiento_kg_ha) / NULLIF(AVG(f.rendimiento_kg_ha), 0) AS coeficiente_variacion
    FROM fact_produccion f
    JOIN dim_lote l ON f.lote_id = l.id
    -- JOIN adicional si el suelo viene de dim_campo o similar
    -- JOIN dim_campo c ON l.campo_id = c.id
    GROUP BY l.id, c.nombre
),
segmentacion AS (
    SELECT 
        lote_id,
        tipo_suelo,
        rendimiento_promedio,
        coeficiente_variacion,
        NTILE(3) OVER (ORDER BY rendimiento_promedio DESC) AS grupo_rendimiento
    FROM rendimiento_por_lote
)
SELECT 
    lote_id,
    tipo_suelo,
    ROUND(rendimiento_promedio::numeric, 2) AS rendimiento_avg_kg_ha,
    ROUND(coeficiente_variacion::numeric, 4) AS riesgo_cv,
    CASE grupo_rendimiento
        WHEN 1 THEN 'Alto Rendimiento'
        WHEN 2 THEN 'Medio'
        WHEN 3 THEN 'Bajo / Alto Riesgo'
    END AS clasificacion
FROM segmentacion
ORDER BY grupo_rendimiento ASC, rendimiento_promedio DESC;
