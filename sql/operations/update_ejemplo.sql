-- ============================================================
-- OPERACIÓN: Actualización (Ítem 4.4 de la consigna)
-- ============================================================
-- ETL Context: El UPDATE en un DW ocurre cuando el ETL detecta
-- que un valor procesado anteriormente era incorrecto (precio
-- de mercado corregido, lectura de sensor fuera de rango, etc.)
-- Se usa ON CONFLICT DO UPDATE (UPSERT) para garantizar
-- idempotencia: si el pipeline corre dos veces, no duplica datos.
-- ============================================================

-- Ejemplo A: Actualizar precio de venta tras corrección de mercado
UPDATE fact_produccion
SET    precio_venta_tn = 362.50,
       updated_at      = NOW()
WHERE  tiempo_id  = (SELECT id FROM dim_tiempo WHERE campania = '2024/2025' LIMIT 1)
AND    cultivo_id = (SELECT id FROM dim_cultivo LIMIT 1);

-- Verificar el resultado
SELECT f.id, t.campania, c.variedad, f.precio_venta_tn, f.updated_at
FROM   fact_produccion f
JOIN   dim_tiempo  t ON t.id = f.tiempo_id
JOIN   dim_cultivo c ON c.id = f.cultivo_id
WHERE  t.campania = '2024/2025'
LIMIT  5;

-- Ejemplo B: UPSERT en dim_clima (patrón del ETL)
-- Esto es exactamente lo que hace el loader del pipeline cada día
INSERT INTO dim_clima (localidad_id, fecha, temp_promedio, humedad_promedio)
VALUES (1, CURRENT_DATE, 22.5, 65.3)
ON CONFLICT (localidad_id, fecha) DO UPDATE SET
    temp_promedio    = EXCLUDED.temp_promedio,
    humedad_promedio = EXCLUDED.humedad_promedio,
    created_at       = NOW();
