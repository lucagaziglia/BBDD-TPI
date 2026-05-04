-- ============================================================
-- BI: Evolución de rendimiento por campaña (Dashboard elemento 1)
-- ============================================================
-- Campaña agrícola = jul (año X) → jun (año X+1).
-- Se deriva en SQL desde dim_tiempo (no hay columna campania).
-- Se distingue Soja vs Trigo a partir del prefijo de cultivo.
-- ============================================================

WITH fact_campania AS (
    SELECT
        f.rendimiento_kg_ha,
        c.cultivo,
        CASE
            WHEN t.mes >= 7
                THEN t."año"::TEXT || '/' || (t."año" + 1)::TEXT
            ELSE (t."año" - 1)::TEXT || '/' || t."año"::TEXT
        END                                            AS campania,
        CASE
            WHEN c.cultivo LIKE 'Soja%'  THEN 'Soja'
            WHEN c.cultivo LIKE 'Trigo%' THEN 'Trigo'
            ELSE 'Otro'
        END                                            AS tipo_cultivo
    FROM   fact_produccion f
    JOIN   dim_tiempo  t ON t.tiempo_id  = f.tiempo_id
    JOIN   dim_cultivo c ON c.id_cultivo = f.id_cultivo
)
SELECT
    campania,
    tipo_cultivo,
    COUNT(*)                                         AS lotes,
    ROUND(AVG(rendimiento_kg_ha)::numeric, 0)        AS rend_promedio_kg_ha,
    ROUND(MIN(rendimiento_kg_ha)::numeric, 0)        AS rend_min,
    ROUND(MAX(rendimiento_kg_ha)::numeric, 0)        AS rend_max,
    ROUND(STDDEV(rendimiento_kg_ha)::numeric, 0)     AS desv_std
FROM   fact_campania
GROUP  BY campania, tipo_cultivo
ORDER  BY tipo_cultivo, campania;
