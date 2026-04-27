-- ============================================================
-- MINERÍA: Predicción dinámica de rendimiento (Ítem 5.2)
-- Método: Regresión lineal OLS en SQL puro
-- x: humedad_promedio (dim_clima)
-- y: rendimiento_kg_ha (fact_produccion)
-- β₁ = Σ((x-x̄)(y-ȳ)) / Σ((x-x̄)²)
-- β₀ = ȳ - β₁·x̄
-- ============================================================
-- Objetivo: Predecir el rendimiento en función de la humedad
-- promedio del período. Permite identificar el nivel de humedad
-- óptimo y proyectar campañas futuras.
-- ============================================================

WITH datos_base AS (
    SELECT
        c.humedad_promedio AS x,
        f.rendimiento_kg_ha AS y
    FROM fact_produccion f
    JOIN dim_clima c ON f.clima_id = c.id
    WHERE c.humedad_promedio IS NOT NULL
      AND f.rendimiento_kg_ha IS NOT NULL
),
medias AS (
    SELECT
        AVG(x)  AS x_bar,
        AVG(y)  AS y_bar,
        COUNT(*) AS n
    FROM datos_base
),
calculo_componentes AS (
    SELECT
        SUM((d.x - m.x_bar) * (d.y - m.y_bar)) AS covarianza,
        SUM(POWER(d.x - m.x_bar, 2))            AS varianza_x
    FROM datos_base d
    CROSS JOIN medias m
),
coeficientes AS (
    SELECT
        c.covarianza / NULLIF(c.varianza_x, 0) AS beta_1,
        m.y_bar - (c.covarianza / NULLIF(c.varianza_x, 0)) * m.x_bar AS beta_0,
        m.n
    FROM calculo_componentes c
    CROSS JOIN medias m
)
SELECT
    n                                                              AS observaciones,
    ROUND(beta_0::numeric, 4)                                      AS interseccion_beta_0,
    ROUND(beta_1::numeric, 4)                                      AS pendiente_beta_1,
    'Rendimiento = ' || ROUND(beta_0::numeric, 2)
        || ' + ' || ROUND(beta_1::numeric, 2)
        || ' × Humedad'                                            AS ecuacion_modelo,
    -- Predicciones de ejemplo para distintos niveles de humedad
    ROUND((beta_0 + beta_1 * 30)::numeric, 0)                     AS pred_humedad_30pct,
    ROUND((beta_0 + beta_1 * 50)::numeric, 0)                     AS pred_humedad_50pct,
    ROUND((beta_0 + beta_1 * 70)::numeric, 0)                     AS pred_humedad_70pct
FROM coeficientes;
