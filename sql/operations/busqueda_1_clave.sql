-- ============================================================
-- OPERACIÓN: Búsqueda por 1 clave (Ítem 4.5 de la consigna)
-- ============================================================
-- Búsqueda por clave primaria simple. Usa el índice de PK → O(log n).
-- ============================================================

-- Ejemplo A: Buscar un lote por su lote_id
SELECT
    l.lote_id,
    l.nombre,
    l.superficie_ha,
    ts.nombre        AS tipo_suelo,
    ca.nombre        AS campo,
    pr.cuit          AS propietario_cuit
FROM  dim_lote        l
JOIN  dim_campo       ca ON ca.campo_id        = l.campo_id
JOIN  dim_propietario pr ON pr.propietario_id  = ca.propietario_id
JOIN  dim_tipo_suelo  ts ON ts.tipo_suelo_id   = l.tipo_suelo_id
WHERE l.lote_id = 1;

-- Ejemplo B: Buscar un hecho de producción por su id
SELECT
    f.id,
    f.rendimiento_kg_ha,
    f.superficie_cosechada_ha,
    f.previo_venta_tn_prom,
    t.fecha,
    l.nombre  AS lote,
    c.cultivo
FROM  fact_produccion f
JOIN  dim_tiempo  t ON t.tiempo_id  = f.tiempo_id
JOIN  dim_lote    l ON l.lote_id    = f.lote_id
JOIN  dim_cultivo c ON c.id_cultivo = f.id_cultivo
WHERE f.id = 1;

-- Ver el plan de ejecución (confirma uso de índice)
EXPLAIN ANALYZE
SELECT * FROM fact_produccion WHERE id = 1;
