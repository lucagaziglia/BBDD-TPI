-- ============================================================
-- OPERACIÓN: Eliminación (Ítem 4.2 de la consigna)
-- ============================================================
-- ETL Context: En un DW raramente se eliminan filas — se hace
-- "baja lógica" marcando el registro como inactivo.
-- Solo se elimina físicamente en casos de error de carga o
-- datos duplicados detectados en el proceso ETL.
-- ============================================================

-- Ejemplo A: Baja lógica (recomendado en DW)
-- Marca un lote como inactivo sin borrar el historial
UPDATE dim_lote
SET    activo     = FALSE,
       updated_at = NOW()
WHERE  lote_id = 11;  -- Lote 3 - La Barrancosa (suelo arenoso, bajo rendimiento)

-- Verificar el resultado
SELECT l.lote_id, l.nombre, ts.nombre AS tipo_suelo, l.activo
FROM   dim_lote      l
JOIN   dim_tipo_suelo ts ON ts.tipo_suelo_id = l.tipo_suelo_id
WHERE  l.lote_id = 11;

-- Ejemplo B: Eliminación física (solo para corregir errores ETL)
-- PRECAUCIÓN: eliminar de fact_produccion y dim_clima primero por integridad referencial
-- DELETE FROM fact_produccion WHERE lote_id = 11;
-- DELETE FROM dim_clima       WHERE lote_id = 11;
-- DELETE FROM dim_lote        WHERE lote_id = 11;
