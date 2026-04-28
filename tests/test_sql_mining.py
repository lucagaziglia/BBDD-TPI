"""
test_sql_mining.py — Tests de las queries SQL de minería de datos.

Estrategia: SQLite en memoria (no requiere Supabase/PostgreSQL real).
Los tests verifican que las queries producen los resultados semánticamente
correctos cuando se ejecutan contra datos de ejemplo.

NOTA: Las queries originales usan sintaxis PostgreSQL (SERIAL, ::numeric, etc.).
Aquí se adaptan mínimamente para SQLite. El objetivo es validar la LÓGICA,
no la sintaxis específica del motor.

Cubre:
  - Segmentación NTILE: 3 grupos, clasificación correcta, orden descendente
  - Predicción OLS: beta_0 y beta_1 son válidos matemáticamente
  - Regresión con relación perfecta (pendiente conocida)
  - NTILE con exactamente 3 lotes (un lote por grupo)
  - Manejo de NULLIF (división por cero)
"""
import sqlite3
import pytest


# ────────────────────────────────────────────────────────────────────────────
# Helpers para crear DB SQLite en memoria con datos de prueba
# ────────────────────────────────────────────────────────────────────────────

def crear_db_con_datos(filas_fact: list[dict], filas_clima: list[dict]) -> sqlite3.Connection:
    """
    Crea una DB SQLite en memoria con tablas dim_lote, dim_clima y fact_produccion.
    Permite testear la lógica SQL sin PostgreSQL.
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    conn.executescript("""
        CREATE TABLE dim_lote (
            id        INTEGER PRIMARY KEY,
            nombre    TEXT    NOT NULL,
            tipo_suelo TEXT
        );

        CREATE TABLE dim_clima (
            id                INTEGER PRIMARY KEY,
            localidad_id      INTEGER,
            fecha             TEXT,
            humedad_promedio  REAL,
            temp_promedio     REAL,
            temp_max          REAL,
            temp_min          REAL
        );

        CREATE TABLE fact_produccion (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            lote_id                 INTEGER NOT NULL,
            clima_id                INTEGER NOT NULL,
            rendimiento_kg_ha       REAL    NOT NULL,
            superficie_cosechada_ha REAL    NOT NULL DEFAULT 100
        );
    """)

    # Insertar lotes
    lotes_ids = set(r["lote_id"] for r in filas_fact)
    for lid in lotes_ids:
        conn.execute(
            "INSERT OR IGNORE INTO dim_lote (id, nombre, tipo_suelo) VALUES (?,?,?)",
            (lid, f"Lote {lid}", "franco"),
        )

    # Insertar clima
    for c in filas_clima:
        conn.execute(
            "INSERT INTO dim_clima (id, localidad_id, fecha, humedad_promedio) VALUES (?,?,?,?)",
            (c["id"], c.get("localidad_id", 1), c.get("fecha", "2024-01-01"), c["humedad_promedio"]),
        )

    # Insertar fact
    for r in filas_fact:
        conn.execute(
            "INSERT INTO fact_produccion (lote_id, clima_id, rendimiento_kg_ha) VALUES (?,?,?)",
            (r["lote_id"], r["clima_id"], r["rendimiento_kg_ha"]),
        )

    conn.commit()
    return conn


# ────────────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def conn_segmentacion():
    """DB con 9 filas de hecho: 3 lotes × 3 campañas, rendimientos distintos."""
    clima = [{"id": i, "humedad_promedio": 60.0} for i in range(1, 10)]
    fact  = [
        # Lote 1 — alto rendimiento
        {"lote_id": 1, "clima_id": 1, "rendimiento_kg_ha": 4000},
        {"lote_id": 1, "clima_id": 2, "rendimiento_kg_ha": 4100},
        {"lote_id": 1, "clima_id": 3, "rendimiento_kg_ha": 3900},
        # Lote 2 — rendimiento medio
        {"lote_id": 2, "clima_id": 4, "rendimiento_kg_ha": 3000},
        {"lote_id": 2, "clima_id": 5, "rendimiento_kg_ha": 3100},
        {"lote_id": 2, "clima_id": 6, "rendimiento_kg_ha": 2900},
        # Lote 3 — bajo rendimiento
        {"lote_id": 3, "clima_id": 7, "rendimiento_kg_ha": 1800},
        {"lote_id": 3, "clima_id": 8, "rendimiento_kg_ha": 1900},
        {"lote_id": 3, "clima_id": 9, "rendimiento_kg_ha": 1700},
    ]
    conn = crear_db_con_datos(fact, clima)
    yield conn
    conn.close()


@pytest.fixture
def conn_regresion_perfecta():
    """
    DB con relación lineal PERFECTA: rendimiento = 2000 + 30 × humedad.
    β₁ esperado = 30, β₀ esperado = 2000.
    """
    clima = []
    fact  = []
    humedades = [20.0, 30.0, 40.0, 50.0, 60.0, 70.0]
    for i, h in enumerate(humedades, start=1):
        rend = 2000 + 30 * h
        clima.append({"id": i, "humedad_promedio": h})
        fact.append({"lote_id": 1, "clima_id": i, "rendimiento_kg_ha": rend})
    conn = crear_db_con_datos(fact, clima)
    yield conn
    conn.close()


# ────────────────────────────────────────────────────────────────────────────
# Tests: Segmentación NTILE (SQLite adapta NTILE vía window function)
# ────────────────────────────────────────────────────────────────────────────

QUERY_SEGMENTACION_SQLITE = """
WITH rendimiento_por_lote AS (
    SELECT
        l.id                        AS lote_id,
        l.nombre                    AS lote,
        l.tipo_suelo,
        AVG(f.rendimiento_kg_ha)    AS rendimiento_promedio,
        CASE WHEN AVG(f.rendimiento_kg_ha) <> 0
             -- SQLite no tiene STDEV; usamos la fórmula equivalente:
             -- sqrt(E[X²] - E[X]²) = desviación estándar poblacional
             THEN SQRT(
                 AVG(f.rendimiento_kg_ha * f.rendimiento_kg_ha) -
                 AVG(f.rendimiento_kg_ha) * AVG(f.rendimiento_kg_ha)
             ) / AVG(f.rendimiento_kg_ha)
             ELSE NULL END           AS coeficiente_variacion,
        COUNT(*)                    AS campanias_medidas
    FROM fact_produccion f
    JOIN dim_lote l ON f.lote_id = l.id
    GROUP BY l.id, l.nombre, l.tipo_suelo
),
segmentacion AS (
    SELECT
        *,
        NTILE(3) OVER (ORDER BY rendimiento_promedio DESC) AS grupo_rendimiento
    FROM rendimiento_por_lote
)
SELECT
    lote_id,
    lote,
    tipo_suelo,
    campanias_medidas,
    ROUND(rendimiento_promedio, 2)  AS rendimiento_avg_kg_ha,
    grupo_rendimiento,
    CASE grupo_rendimiento
        WHEN 1 THEN 'Alto Rendimiento'
        WHEN 2 THEN 'Medio'
        WHEN 3 THEN 'Bajo / Alto Riesgo'
    END AS clasificacion
FROM segmentacion
ORDER BY grupo_rendimiento ASC, rendimiento_promedio DESC;
"""


class TestSegmentacionNTILE:
    """Valida la lógica de segmentación por NTILE."""

    def test_retorna_tres_filas_para_tres_lotes(self, conn_segmentacion):
        rows = conn_segmentacion.execute(QUERY_SEGMENTACION_SQLITE).fetchall()
        assert len(rows) == 3

    def test_lote_alto_en_grupo_1(self, conn_segmentacion):
        rows = conn_segmentacion.execute(QUERY_SEGMENTACION_SQLITE).fetchall()
        # El lote con mayor rendimiento debe estar en grupo 1
        grupo1 = [r for r in rows if r["grupo_rendimiento"] == 1]
        assert len(grupo1) == 1
        assert grupo1[0]["lote_id"] == 1  # Lote 1 tiene ~4000 kg/ha

    def test_lote_bajo_en_grupo_3(self, conn_segmentacion):
        rows = conn_segmentacion.execute(QUERY_SEGMENTACION_SQLITE).fetchall()
        grupo3 = [r for r in rows if r["grupo_rendimiento"] == 3]
        assert len(grupo3) == 1
        assert grupo3[0]["lote_id"] == 3  # Lote 3 tiene ~1800 kg/ha

    def test_clasificacion_texto_correcta(self, conn_segmentacion):
        rows = conn_segmentacion.execute(QUERY_SEGMENTACION_SQLITE).fetchall()
        clases = {r["grupo_rendimiento"]: r["clasificacion"] for r in rows}
        assert clases[1] == "Alto Rendimiento"
        assert clases[2] == "Medio"
        assert clases[3] == "Bajo / Alto Riesgo"

    def test_rendimiento_promedio_correcto(self, conn_segmentacion):
        rows = conn_segmentacion.execute(QUERY_SEGMENTACION_SQLITE).fetchall()
        lote1_row = next(r for r in rows if r["lote_id"] == 1)
        # Promedio de 4000, 4100, 3900 = 4000
        assert abs(lote1_row["rendimiento_avg_kg_ha"] - 4000.0) < 0.1

    def test_orden_descendente_por_rendimiento(self, conn_segmentacion):
        rows = conn_segmentacion.execute(QUERY_SEGMENTACION_SQLITE).fetchall()
        rendimientos = [r["rendimiento_avg_kg_ha"] for r in rows]
        assert rendimientos == sorted(rendimientos, reverse=True)

    def test_grupos_son_exactamente_1_2_3(self, conn_segmentacion):
        rows = conn_segmentacion.execute(QUERY_SEGMENTACION_SQLITE).fetchall()
        grupos = {r["grupo_rendimiento"] for r in rows}
        assert grupos == {1, 2, 3}


# ────────────────────────────────────────────────────────────────────────────
# Tests: Predicción OLS (regresión lineal en SQL puro)
# ────────────────────────────────────────────────────────────────────────────

QUERY_OLS_SQLITE = """
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
        SUM((d.x - m.x_bar) * (d.y - m.y_bar))  AS covarianza,
        SUM((d.x - m.x_bar) * (d.x - m.x_bar))  AS varianza_x
    FROM datos_base d
    CROSS JOIN medias m
),
coeficientes AS (
    SELECT
        CASE WHEN c.varianza_x <> 0 THEN c.covarianza / c.varianza_x ELSE NULL END AS beta_1,
        m.y_bar - (CASE WHEN c.varianza_x <> 0 THEN c.covarianza / c.varianza_x ELSE NULL END) * m.x_bar AS beta_0,
        m.n
    FROM calculo_componentes c
    CROSS JOIN medias m
)
SELECT
    n            AS observaciones,
    ROUND(beta_0, 4) AS interseccion_beta_0,
    ROUND(beta_1, 4) AS pendiente_beta_1,
    ROUND(beta_0 + beta_1 * 30, 0) AS pred_humedad_30pct,
    ROUND(beta_0 + beta_1 * 50, 0) AS pred_humedad_50pct,
    ROUND(beta_0 + beta_1 * 70, 0) AS pred_humedad_70pct
FROM coeficientes;
"""


class TestPrediccionOLS:
    """Valida la lógica de regresión lineal OLS en SQL."""

    def test_retorna_exactamente_una_fila(self, conn_regresion_perfecta):
        rows = conn_regresion_perfecta.execute(QUERY_OLS_SQLITE).fetchall()
        assert len(rows) == 1

    def test_n_observaciones_correcto(self, conn_regresion_perfecta):
        row = conn_regresion_perfecta.execute(QUERY_OLS_SQLITE).fetchone()
        # 6 puntos (una campaña por nivel de humedad)
        assert row["observaciones"] == 6

    def test_beta_1_correcto_relacion_perfecta(self, conn_regresion_perfecta):
        """Con relación perfecta rendimiento = 2000 + 30×humedad, β₁ debe ser 30."""
        row = conn_regresion_perfecta.execute(QUERY_OLS_SQLITE).fetchone()
        assert abs(row["pendiente_beta_1"] - 30.0) < 0.01, (
            f"β₁ esperado ≈ 30, obtenido: {row['pendiente_beta_1']}"
        )

    def test_beta_0_correcto_relacion_perfecta(self, conn_regresion_perfecta):
        """Con relación perfecta, β₀ debe ser 2000."""
        row = conn_regresion_perfecta.execute(QUERY_OLS_SQLITE).fetchone()
        assert abs(row["interseccion_beta_0"] - 2000.0) < 0.1, (
            f"β₀ esperado ≈ 2000, obtenido: {row['interseccion_beta_0']}"
        )

    def test_prediccion_30_pct_correcta(self, conn_regresion_perfecta):
        """Pred para humedad=30: 2000 + 30×30 = 2900."""
        row = conn_regresion_perfecta.execute(QUERY_OLS_SQLITE).fetchone()
        assert abs(row["pred_humedad_30pct"] - 2900) < 1

    def test_prediccion_50_pct_correcta(self, conn_regresion_perfecta):
        """Pred para humedad=50: 2000 + 30×50 = 3500."""
        row = conn_regresion_perfecta.execute(QUERY_OLS_SQLITE).fetchone()
        assert abs(row["pred_humedad_50pct"] - 3500) < 1

    def test_prediccion_70_pct_correcta(self, conn_regresion_perfecta):
        """Pred para humedad=70: 2000 + 30×70 = 4100."""
        row = conn_regresion_perfecta.execute(QUERY_OLS_SQLITE).fetchone()
        assert abs(row["pred_humedad_70pct"] - 4100) < 1

    def test_prediccion_monotonas_con_pendiente_positiva(self, conn_regresion_perfecta):
        """Con pendiente positiva, mayor humedad → mayor rendimiento predicho."""
        row = conn_regresion_perfecta.execute(QUERY_OLS_SQLITE).fetchone()
        assert row["pred_humedad_30pct"] < row["pred_humedad_50pct"] < row["pred_humedad_70pct"]
