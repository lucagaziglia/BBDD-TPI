-- ============================================================
-- BI: Evolución de rendimiento por campaña (Dashboard elemento 1)
-- ============================================================
SELECT
    t.campania,
    ct.nombre                                        AS cultivo,
    COUNT(*)                                         AS lotes,
    ROUND(AVG(f.rendimiento_kg_ha)::numeric, 0)      AS rend_promedio_kg_ha,
    ROUND(MIN(f.rendimiento_kg_ha)::numeric, 0)      AS rend_min,
    ROUND(MAX(f.rendimiento_kg_ha)::numeric, 0)      AS rend_max,
    ROUND(STDDEV(f.rendimiento_kg_ha)::numeric, 0)   AS desv_std
FROM   fact_produccion f
JOIN   dim_tiempo       t  ON t.id  = f.tiempo_id
JOIN   dim_cultivo      cv ON cv.id = f.cultivo_id
JOIN   dim_tipo_cultivo ct ON ct.id = cv.tipo_cultivo_id
GROUP  BY t.campania, ct.nombre
ORDER  BY ct.nombre, t.campania;
