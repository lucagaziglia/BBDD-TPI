-- ============================================================
-- BI: Producción total por propietario (Dashboard elemento 2)
-- ============================================================
-- dim_propietario no tiene razón social en el nuevo esquema:
-- se identifica por CUIT y email.
-- ============================================================

WITH fact_campania AS (
    SELECT
        f.lote_id,
        f.rendimiento_kg_ha,
        f.superficie_cosechada_ha,
        CASE
            WHEN t.mes >= 7
                THEN t."año"::TEXT || '/' || (t."año" + 1)::TEXT
            ELSE (t."año" - 1)::TEXT || '/' || t."año"::TEXT
        END AS campania
    FROM   fact_produccion f
    JOIN   dim_tiempo t ON t.tiempo_id = f.tiempo_id
)
SELECT
    pr.cuit                                                       AS propietario_cuit,
    pr.email                                                      AS propietario_email,
    fc.campania,
    COUNT(DISTINCT l.lote_id)                                     AS lotes,
    ROUND(AVG(fc.rendimiento_kg_ha)::numeric, 0)                  AS rend_promedio,
    ROUND(SUM(fc.rendimiento_kg_ha *
              fc.superficie_cosechada_ha / 1000)::numeric, 1)     AS produccion_tn
FROM   fact_campania    fc
JOIN   dim_lote         l  ON l.lote_id        = fc.lote_id
JOIN   dim_campo        ca ON ca.campo_id      = l.campo_id
JOIN   dim_propietario  pr ON pr.propietario_id = ca.propietario_id
GROUP  BY pr.cuit, pr.email, fc.campania
ORDER  BY pr.cuit, fc.campania;
