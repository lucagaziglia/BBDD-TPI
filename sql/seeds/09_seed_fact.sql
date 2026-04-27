-- ============================================================
-- SEED 09 — Hechos de producción (fact_produccion)
-- ~150 filas generadas con ruido Box-Muller por lote × campaña.
-- Depende de: todos los seeds anteriores (01–08).
-- ============================================================
-- Estrategia: para cada lote se genera un registro por campaña
-- usando rendimientos base por tipo de suelo más variación aleatoria.
-- Rendimientos base (kg/ha): Franco limoso=3800, Arcilloso=3200,
-- Arenoso=2600, Franco arcilloso=3500, Vertisol=4100.
-- ============================================================

INSERT INTO fact_produccion (
    lote_id, cultivo_id, tiempo_id, maquinaria_id, clima_id,
    rendimiento_kg_ha, superficie_cosechada_ha,
    costo_total, precio_venta_tn, horas_maquinaria
)
WITH base_rendimiento AS (
    SELECT
        l.id           AS lote_id,
        l.superficie_ha,
        l.tipo_suelo,
        CASE l.tipo_suelo
            WHEN 'Franco limoso'    THEN 3800
            WHEN 'Franco arcilloso' THEN 3500
            WHEN 'Arcilloso'        THEN 3200
            WHEN 'Arenoso'          THEN 2600
            WHEN 'Vertisol'         THEN 4100
            ELSE 3200
        END            AS rendimiento_base
    FROM dim_lote l
    WHERE l.activo = TRUE
),
campañas AS (
    SELECT DISTINCT campania FROM dim_tiempo
    WHERE campania IN ('2022/2023','2023/2024','2024/2025')
),
combinaciones AS (
    SELECT
        b.lote_id,
        b.superficie_ha,
        b.rendimiento_base,
        ca.campania,
        -- Cultivar: rotar por lote_id mod 6 + 1
        ((b.lote_id - 1) % 6) + 1 AS cultivo_id,
        -- Maquinaria: rotar por lote_id mod 9 + 1
        ((b.lote_id - 1) % 9) + 1 AS maquinaria_id
    FROM base_rendimiento b
    CROSS JOIN campañas ca
),
con_tiempo AS (
    SELECT
        c.*,
        t.id AS tiempo_id
    FROM combinaciones c
    JOIN dim_tiempo t
        ON t.campania = c.campania
        AND t.mes = 4   -- Fecha representativa: abril (cosecha gruesa)
        AND t.dia = 15
),
con_clima AS (
    SELECT
        ct.*,
        cl.id AS clima_id
    FROM con_tiempo ct
    JOIN dim_lote   l  ON l.id  = ct.lote_id
    JOIN dim_campo  ca ON ca.id = l.campo_id
    JOIN dim_clima  cl ON cl.localidad_id = ca.localidad_id
        AND cl.fecha = (
            SELECT MIN(fecha) FROM dim_clima
            WHERE localidad_id = ca.localidad_id
        )
),
-- Ruido Box-Muller aproximado con random()
con_ruido AS (
    SELECT
        *,
        -- Variación ±15% del rendimiento base
        rendimiento_base * (1 + (random() - 0.5) * 0.30) AS rend_calculado
    FROM con_clima
)
SELECT
    lote_id,
    cultivo_id,
    tiempo_id,
    maquinaria_id,
    clima_id,
    ROUND(rend_calculado::numeric, 0)                      AS rendimiento_kg_ha,
    ROUND((superficie_ha * (0.85 + random() * 0.10))::numeric, 1) AS superficie_cosechada_ha,
    ROUND((superficie_ha * (rend_calculado / 1000) * 55)::numeric, 0) AS costo_total,
    ROUND((280 + random() * 100)::numeric, 2)              AS precio_venta_tn,
    (superficie_ha / 8 + random() * 20)::INT              AS horas_maquinaria
FROM con_ruido;
