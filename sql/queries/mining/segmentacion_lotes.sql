-- ============================================================
-- MINERÍA: Segmentación dinámica de lotes (Ítem 5.1)
-- Método: NTILE + rankings en SQL puro
-- Variables: rendimiento_kg_ha, coeficiente de variación, tipo_suelo
-- Grupos: alto rendimiento / rendimiento medio / bajo riesgo
-- ============================================================
-- Objetivo: Clasificar los lotes en 3 grupos (terciles) según su
-- rendimiento histórico promedio. Segmenta en: Premium, Estándar
-- y Riesgosos. El CV (coeficiente de variación) mide inestabilidad.
-- ============================================================

WITH rendimiento_por_lote AS (
    SELECT
        l.id                                                 AS lote_id,
        l.nombre                                             AS lote,
        l.tipo_suelo,
        AVG(f.rendimiento_kg_ha)                             AS rendimiento_promedio,
        STDDEV(f.rendimiento_kg_ha) /
            NULLIF(AVG(f.rendimiento_kg_ha), 0)              AS coeficiente_variacion,
        COUNT(*)                                             AS campañas_medidas
    FROM fact_produccion f
    JOIN dim_lote l ON f.lote_id = l.id
    GROUP BY l.id, l.nombre, l.tipo_suelo
),
segmentacion AS (
    SELECT
        *,
        NTILE(3) OVER (ORDER BY rendimiento_promedio DESC) AS grupo_rendimiento
    FROM rendimiento_por_lote
)
SELECT
    lote_id,
    lote,
    tipo_suelo,
    campañas_medidas,
    ROUND(rendimiento_promedio::numeric,  2) AS rendimiento_avg_kg_ha,
    ROUND(coeficiente_variacion::numeric, 4) AS riesgo_cv,
    CASE grupo_rendimiento
        WHEN 1 THEN 'Alto Rendimiento'
        WHEN 2 THEN 'Medio'
        WHEN 3 THEN 'Bajo / Alto Riesgo'
    END AS clasificacion
FROM segmentacion
ORDER BY grupo_rendimiento ASC, rendimiento_promedio DESC;
