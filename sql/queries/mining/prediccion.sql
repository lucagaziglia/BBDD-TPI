-- ==============================================================================
-- Predicción Dinámica (Regresión Lineal Simple OLS) - Minería de Datos (Ítem 5)
-- ==============================================================================
-- Objetivo: Predecir el rendimiento (Y) en función de la humedad promedio (X).
-- Fórmula OLS: 
-- β₁ (Pendiente) = Σ((x - x̄)(y - ȳ)) / Σ((x - x̄)²)
-- β₀ (Intersección) = ȳ - β₁ * x̄

WITH datos_base AS (
    SELECT 
        c.humedad_promedio AS x,
        f.rendimiento_kg_ha AS y
    FROM fact_produccion f
    -- Join considerando que la FK corregida es por localidad (o en su defecto el clima mapeado al hecho)
    JOIN dim_clima c ON f.clima_id = c.id
    WHERE c.humedad_promedio IS NOT NULL AND f.rendimiento_kg_ha IS NOT NULL
),
medias AS (
    SELECT 
        AVG(x) AS x_bar,
        AVG(y) AS y_bar,
        COUNT(*) AS n
    FROM datos_base
),
calculo_componentes AS (
    SELECT 
        SUM((d.x - m.x_bar) * (d.y - m.y_bar)) AS covarianza,
        SUM(POWER(d.x - m.x_bar, 2)) AS varianza_x
    FROM datos_base d
    CROSS JOIN medias m
),
coeficientes AS (
    SELECT 
        c.covarianza / NULLIF(c.varianza_x, 0) AS beta_1,
        m.y_bar - (c.covarianza / NULLIF(c.varianza_x, 0)) * m.x_bar AS beta_0
    FROM calculo_componentes c
    CROSS JOIN medias m
)
-- Mostrar el modelo final y un ejemplo de predicción
SELECT 
    ROUND(beta_0::numeric, 4) AS interseccion_beta_0,
    ROUND(beta_1::numeric, 4) AS pendiente_beta_1,
    'Rendimiento = ' || ROUND(beta_0::numeric, 2) || ' + ' || ROUND(beta_1::numeric, 2) || ' * Humedad' AS ecuacion_modelo,
    
    -- Predicción de prueba (ej. Si la humedad es 40%)
    ROUND((beta_0 + beta_1 * 40)::numeric, 2) AS prediccion_humedad_40
FROM coeficientes;
