-- ============================================================
-- SEED 11 — Hechos de producción (fact_produccion) — 150 filas
-- 25 lotes × 3 campañas × 2 cultivos (soja + trigo) = 150
-- Depende de: 08_seed_lotes.sql, 09_seed_maquinaria.sql,
--             04_seed_tiempo.sql, 03_seed_tipos.sql (cultivos).
-- ============================================================
-- Rendimiento base por tipo de suelo (kg/ha):
--   Franco          = 3700      Franco limoso    = 3800
--   Franco arcilloso= 3500      Arcilloso        = 3200
--   Arenoso         = 2600      Vertisol         = 4100
-- Factor por campaña: 2022/23=1.00, 2023/24=0.82 (sequía), 2024/25=1.07
-- Variación aleatoria ±15% (Box-Muller aproximado con random()).
-- ============================================================

INSERT INTO fact_produccion (
    maquinaria_id, id_cultivo, lote_id, tiempo_id,
    rendimiento_kg_ha, superficie_cosechada_ha,
    costo_total, previo_venta_tn_prom
)
WITH base_rendimiento AS (
    SELECT
        l.lote_id,
        l.superficie_ha,
        ts.nombre AS tipo_suelo,
        CASE ts.nombre
            WHEN 'Franco'           THEN 3700
            WHEN 'Franco limoso'    THEN 3800
            WHEN 'Franco arcilloso' THEN 3500
            WHEN 'Arcilloso'        THEN 3200
            WHEN 'Arenoso'          THEN 2600
            WHEN 'Vertisol'         THEN 4100
            ELSE 3200
        END AS rend_base
    FROM dim_lote l
    JOIN dim_tipo_suelo ts ON ts.tipo_suelo_id = l.tipo_suelo_id
    WHERE l.activo = TRUE
),
campañas AS (
    -- (anio_inicio_campania, mes_cosecha, anio_cosecha, factor, es_soja)
    SELECT * FROM (VALUES
        (2022, 4,  2023, 1.00, TRUE),   -- Soja 22/23 cosecha abr-23
        (2022, 11, 2022, 1.00, FALSE),  -- Trigo 22/23 cosecha nov-22
        (2023, 4,  2024, 0.82, TRUE),   -- Soja 23/24 cosecha abr-24 (sequía)
        (2023, 11, 2023, 0.82, FALSE),  -- Trigo 23/24 cosecha nov-23 (sequía)
        (2024, 4,  2025, 1.07, TRUE),   -- Soja 24/25 cosecha abr-25
        (2024, 11, 2024, 1.07, FALSE)   -- Trigo 24/25 cosecha nov-24
    ) AS v(anio_camp, mes_cosecha, anio_cosecha, factor, es_soja)
),
combinaciones AS (
    SELECT
        b.lote_id,
        b.superficie_ha,
        b.rend_base,
        ca.anio_camp,
        ca.mes_cosecha,
        ca.anio_cosecha,
        ca.factor,
        ca.es_soja,
        -- Maquinaria rotada por lote (1..9)
        ((b.lote_id - 1) % 9) + 1 AS maquinaria_id,
        -- Cultivo: soja 1-3, trigo 4-6 — rotamos dentro del grupo
        CASE WHEN ca.es_soja
             THEN ((b.lote_id - 1) % 3) + 1            -- soja: 1-3
             ELSE ((b.lote_id - 1) % 3) + 4            -- trigo: 4-6
        END AS id_cultivo
    FROM base_rendimiento b
    CROSS JOIN campañas ca
),
con_tiempo AS (
    SELECT
        c.*,
        t.tiempo_id
    FROM combinaciones c
    JOIN dim_tiempo t
      ON EXTRACT(YEAR  FROM t.fecha)::INT = c.anio_cosecha
     AND EXTRACT(MONTH FROM t.fecha)::INT = c.mes_cosecha
),
con_ruido AS (
    SELECT
        *,
        rend_base * factor * (1 + (RANDOM() - 0.5) * 0.30) AS rend_calculado
    FROM con_tiempo
)
SELECT
    maquinaria_id,
    id_cultivo,
    lote_id,
    tiempo_id,
    ROUND(rend_calculado::numeric, 0)                                AS rendimiento_kg_ha,
    ROUND((superficie_ha * (0.85 + RANDOM() * 0.10))::numeric, 1)    AS superficie_cosechada_ha,
    ROUND((superficie_ha * (rend_calculado / 1000) * 55)::numeric, 2) AS costo_total,
    -- Soja ~340 USD/tn, Trigo ~260 USD/tn (con ruido ±10%)
    ROUND((CASE WHEN es_soja THEN 340 ELSE 260 END
           * (0.90 + RANDOM() * 0.20))::numeric, 2)                  AS previo_venta_tn_prom
FROM con_ruido;
