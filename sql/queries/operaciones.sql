-- Operaciones DML Faltantes (Ítem 4)

-- ==============================================================================
-- 1. DELETE con explicación ETL (baja lógica de un lote inactivo)
-- ==============================================================================
-- Justificación ETL: En un Datawarehouse rara vez se hace un borrado físico (DELETE) 
-- para no perder la integridad referencial de la tabla de hechos. Si un lote 
-- deja de estar operativo, el ETL detecta el cambio en origen (CRM o ERP) y 
-- aplica una "baja lógica" actualizando un flag en la dimensión.
-- Si la tabla no tiene flag de activo, se usa un DELETE físico (ejemplo abajo).

-- Baja lógica (Recomendada en DW):
-- UPDATE dim_lote SET estado = 'INACTIVO' WHERE id = 15;

-- Borrado físico (Ejemplo puro):
DELETE FROM dim_lote 
WHERE id = 999; -- Se asume un ID que fue cargado por error o no tiene hechos asociados

-- ==============================================================================
-- 2. UPDATE con explicación ETL (actualización de precio_venta_tn)
-- ==============================================================================
-- Justificación ETL: Al finalizar la campaña, el precio de venta final de la 
-- cooperativa puede reajustarse. El ETL de actualización busca los registros 
-- afectados en la fact_table y aplica el nuevo precio para recalcular ingresos.

UPDATE fact_produccion
SET precio_venta_tn = 295.50
WHERE lote_id = 3 AND tiempo_id = (SELECT id FROM dim_tiempo WHERE campana = '2023/24' LIMIT 1);

-- ==============================================================================
-- 3. Búsqueda por 1 clave (SELECT simple)
-- ==============================================================================
-- Buscar toda la información del propietario número 2

SELECT id, nombre, cuit, tipo_sociedad 
FROM dim_propietario
WHERE id = 2;

-- ==============================================================================
-- 4. Búsqueda por 2 claves (SELECT compuesto)
-- ==============================================================================
-- Buscar los rendimientos de un lote específico en una campaña particular

SELECT 
    f.rendimiento_kg_ha,
    f.superficie_cosechada_ha,
    (f.rendimiento_kg_ha * f.superficie_cosechada_ha) AS produccion_total_kg,
    c.nombre AS cultivo_sembrado
FROM fact_produccion f
JOIN dim_cultivo c ON f.cultivo_id = c.id
JOIN dim_tiempo t ON f.tiempo_id = t.id
WHERE f.lote_id = 8 
  AND t.campana = '2024/25';
