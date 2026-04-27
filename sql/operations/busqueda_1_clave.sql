-- ============================================================
-- OPERACIÓN: Búsqueda por 1 clave (Ítem 4.5 de la consigna)
-- ============================================================
-- Búsqueda por clave primaria simple (id).
-- Usa el índice de PK → O(log n), muy eficiente.
-- ============================================================

-- Ejemplo A: Buscar un lote por su id
SELECT
    l.id,
    l.nombre,
    l.superficie_ha,
    l.tipo_suelo,
    ca.nombre AS campo,
    pr.razon_social AS propietario
FROM  dim_lote l
JOIN  dim_campo      ca ON ca.id = l.campo_id
JOIN  dim_propietario pr ON pr.id = ca.propietario_id
WHERE l.id = 1;

-- Ejemplo B: Buscar un hecho de producción por su id
SELECT
    f.id,
    f.rendimiento_kg_ha,
    f.superficie_cosechada_ha,
    f.precio_venta_tn,
    t.campania,
    l.nombre AS lote
FROM  fact_produccion f
JOIN  dim_tiempo t ON t.id = f.tiempo_id
JOIN  dim_lote   l ON l.id = f.lote_id
WHERE f.id = 1;

-- Ver el plan de ejecución (confirma uso de índice)
EXPLAIN ANALYZE
SELECT * FROM fact_produccion WHERE id = 1;
