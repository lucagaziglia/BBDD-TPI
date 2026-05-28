-- Generación de hechos de siembra y cosecha desconectados del tiempo diario
INSERT INTO fact_siembra_cosecha (
    maquinaria_id, cultivo_id, lote_id, rendimiento_kg_ha, 
    superficie_sembrada_cosechada_ha, costo_total, precio_venta_tn_prom, fecha, id_tipo_operacion
)
SELECT 
    1 AS maquinaria_id, 
    1 AS id_cultivo, 
    l.lote_id, 
    ROUND((3500 * (1 + (RANDOM() - 0.5) * 0.30))::numeric, 0) AS rendimiento_kg_ha,
    l.superficie_ha AS superficie_sembrada_cosechada_ha,
    ROUND((l.superficie_ha * 3.5 * 55)::numeric, 2) AS costo_total,
    340.00 AS precio_venta_tn_prom,
    '2024-04-15'::DATE AS fecha,
    2 AS id_tipo_operacion -- Simulamos que esta fila es una "Cosecha"
FROM dim_lote l;