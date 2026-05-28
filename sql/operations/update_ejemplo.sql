-- ============================================================
-- OPERACIÓN: Actualización (Ítem 4.4 de la consigna)
-- ============================================================
-- ETL Context: El UPDATE en un DW ocurre cuando el ETL detecta
-- que un valor procesado anteriormente era incorrecto (precio
-- de mercado corregido, lectura de sensor fuera de rango, etc.)
-- Se usa ON CONFLICT DO UPDATE (UPSERT) para garantizar
-- idempotencia: si el pipeline corre dos veces, no duplica datos.
-- ============================================================

-- Ejemplo A: Actualizar precio promedio de venta tras corrección de mercado
UPDATE fact_produccion
SET    previo_venta_tn_prom = 362.50
WHERE  tiempo_id  IN (
           SELECT tiempo_id FROM dim_tiempo
           WHERE fecha BETWEEN '2024-07-01' AND '2025-06-30'
       )
AND    id_cultivo = (SELECT id_cultivo FROM dim_cultivo
                     WHERE cultivo = 'Soja DM 4612 RR');

-- Verificar el resultado
SELECT f.id, t.fecha, c.cultivo, f.previo_venta_tn_prom
FROM   fact_produccion f
JOIN   dim_tiempo  t ON t.tiempo_id  = f.tiempo_id
JOIN   dim_cultivo c ON c.id_cultivo = f.id_cultivo
WHERE  t.fecha BETWEEN '2024-07-01' AND '2025-06-30'
AND    c.cultivo = 'Soja DM 4612 RR'
LIMIT  5;

-- Ejemplo B: UPSERT en dim_clima (patrón del ETL)
-- Esto es exactamente lo que hace el loader del pipeline cada día
INSERT INTO dim_clima (lote_id, tiempo_id, temp_promedio, humedad_promedio)
VALUES (
    1,
    (SELECT tiempo_id FROM dim_tiempo WHERE fecha = '2024-04-01'),
    22.5,
    65.3
)
ON CONFLICT (lote_id, tiempo_id) DO UPDATE SET
    temp_promedio    = EXCLUDED.temp_promedio,
    humedad_promedio = EXCLUDED.humedad_promedio;
