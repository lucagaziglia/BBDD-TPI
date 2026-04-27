-- Migración 012: Corrección de diseño en dim_clima
-- Problema original: dim_clima apuntaba a lote_id, generando redundancia geométrica y posibles inconsistencias.
-- Solución: El clima es un fenómeno de zona (localidad), no de lote individual.

-- 1. Añadimos la nueva columna de relación con localidad
ALTER TABLE dim_clima 
ADD COLUMN localidad_id INTEGER;

-- 2. Añadimos la restricción de clave foránea
ALTER TABLE dim_clima 
ADD CONSTRAINT fk_dim_clima_localidad 
FOREIGN KEY (localidad_id) REFERENCES dim_localidad(id);

-- 3. (Opcional si hay datos) Migrar los datos existentes:
-- UPDATE dim_clima c 
-- SET localidad_id = (
--     SELECT l.localidad_id 
--     FROM dim_lote l 
--     JOIN dim_campo ca ON l.campo_id = ca.id 
--     WHERE l.id = c.lote_id
-- );

-- 4. Eliminamos la relación antigua con lote_id
ALTER TABLE dim_clima 
DROP COLUMN lote_id;
