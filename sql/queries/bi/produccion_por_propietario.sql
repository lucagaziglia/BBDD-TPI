-- ============================================================
-- BI: Producción total por propietario (Dashboard elemento 2)
-- ============================================================
SELECT
    pr.razon_social                                              AS propietario,
    t.campania,
    COUNT(DISTINCT l.id)                                         AS lotes,
    ROUND(AVG(f.rendimiento_kg_ha)::numeric, 0)                  AS rend_promedio,
    ROUND(SUM(f.rendimiento_kg_ha *
              f.superficie_cosechada_ha / 1000)::numeric, 1)     AS produccion_tn
FROM   fact_produccion f
JOIN   dim_lote         l  ON l.id  = f.lote_id
JOIN   dim_campo        ca ON ca.id = l.campo_id
JOIN   dim_propietario  pr ON pr.id = ca.propietario_id
JOIN   dim_tiempo        t ON t.id  = f.tiempo_id
GROUP  BY pr.razon_social, t.campania
ORDER  BY pr.razon_social, t.campania;
