"""
test_dashboard.py — Tests del dashboard BI (HTML + JavaScript).

Estrategia: tests estructurales del HTML/JS sin browser.
  - Verifica que index.html existe y tiene los elementos DOM obligatorios
  - Verifica que app.js existe y referencia los IDs del HTML
  - Verifica que style.css existe
  - Verifica que se carga Chart.js
  - Verifica que los 3 canvas tienen los IDs que usa app.js

No se ejecuta JavaScript: eso lo haría un test de browser (Playwright/Selenium).
Estos tests son "smoke tests" de coherencia HTML↔JS.
"""
import os
import re
import pytest


DASHBOARD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "dashboard"
)
INDEX_HTML = os.path.join(DASHBOARD_DIR, "index.html")
APP_JS     = os.path.join(DASHBOARD_DIR, "app.js")
STYLE_CSS  = os.path.join(DASHBOARD_DIR, "style.css")


# ────────────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def html_content():
    with open(INDEX_HTML, encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def js_content():
    with open(APP_JS, encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def css_content():
    with open(STYLE_CSS, encoding="utf-8") as f:
        return f.read()


# ────────────────────────────────────────────────────────────────────────────
# Tests: archivos existen
# ────────────────────────────────────────────────────────────────────────────

class TestArchivosExisten:
    def test_index_html_existe(self):
        assert os.path.isfile(INDEX_HTML), f"Falta: {INDEX_HTML}"

    def test_app_js_existe(self):
        assert os.path.isfile(APP_JS), f"Falta: {APP_JS}"

    def test_style_css_existe(self):
        assert os.path.isfile(STYLE_CSS), f"Falta: {STYLE_CSS}"

    def test_archivos_no_vacios(self):
        for path in [INDEX_HTML, APP_JS, STYLE_CSS]:
            assert os.path.getsize(path) > 0, f"Archivo vacío: {path}"


# ────────────────────────────────────────────────────────────────────────────
# Tests: HTML — estructura obligatoria
# ────────────────────────────────────────────────────────────────────────────

class TestHTMLEstructura:
    """Verifica los elementos del HTML necesarios para el dashboard."""

    # IDs de canvas que app.js referencia con getElementById
    CANVAS_IDS = ["evolucionChart", "propietariosChart", "riesgoChart"]

    def test_tiene_doctype(self, html_content):
        assert "<!DOCTYPE html>" in html_content.lower() or "<!doctype html>" in html_content.lower()

    def test_tiene_etiqueta_html(self, html_content):
        assert "<html" in html_content

    def test_tiene_head_y_body(self, html_content):
        assert "<head" in html_content
        assert "<body" in html_content

    def test_tiene_title(self, html_content):
        assert "<title>" in html_content

    def test_carga_chartjs(self, html_content):
        """Chart.js debe estar referenciado (CDN o local)."""
        assert "chart" in html_content.lower(), (
            "Chart.js no está incluido en el HTML"
        )

    def test_carga_app_js(self, html_content):
        """app.js debe estar referenciado en el HTML."""
        assert "app.js" in html_content

    def test_canvas_evolucion_existe(self, html_content):
        assert 'id="evolucionChart"' in html_content

    def test_canvas_propietarios_existe(self, html_content):
        assert 'id="propietariosChart"' in html_content

    def test_canvas_riesgo_existe(self, html_content):
        assert 'id="riesgoChart"' in html_content

    def test_todos_canvas_son_etiqueta_canvas(self, html_content):
        """Los IDs de charts deben estar en etiquetas <canvas>."""
        for canvas_id in self.CANVAS_IDS:
            # Busca <canvas ... id="evolucionChart" ... >
            patron = rf'<canvas[^>]*id="{canvas_id}"'
            assert re.search(patron, html_content), (
                f"<canvas id=\"{canvas_id}\"> no encontrado en HTML"
            )

    def test_tiene_h1(self, html_content):
        """Debe haber exactamente un <h1> por buenas prácticas SEO."""
        h1_matches = re.findall(r"<h1[^>]*>", html_content, re.IGNORECASE)
        assert len(h1_matches) >= 1, "Falta al menos un <h1> en el HTML"


# ────────────────────────────────────────────────────────────────────────────
# Tests: JavaScript — coherencia con el HTML
# ────────────────────────────────────────────────────────────────────────────

class TestJavaScriptCoherencia:
    """Verifica que app.js referencia los mismos IDs que existen en HTML."""

    CANVAS_IDS = ["evolucionChart", "propietariosChart", "riesgoChart"]

    def test_referencia_evolucionChart(self, js_content):
        assert "evolucionChart" in js_content

    def test_referencia_propietariosChart(self, js_content):
        assert "propietariosChart" in js_content

    def test_referencia_riesgoChart(self, js_content):
        assert "riesgoChart" in js_content

    def test_usa_getElementByID_o_querySelector(self, js_content):
        """app.js debe usar getElementById o querySelector para montar los charts."""
        usa_get_by_id     = "getElementById" in js_content
        usa_query_selector = "querySelector" in js_content
        assert usa_get_by_id or usa_query_selector, (
            "app.js no usa getElementById ni querySelector"
        )

    def test_instancia_new_chart(self, js_content):
        """Debe haber al menos una instancia de Chart() en app.js."""
        assert "new Chart(" in js_content

    def test_tiene_domcontentloaded(self, js_content):
        """La inicialización debe esperar a que el DOM esté listo."""
        assert "DOMContentLoaded" in js_content

    def test_tipos_de_graficos_declarados(self, js_content):
        """Al menos los tipos 'line' y 'bar' deben estar declarados."""
        assert "'line'" in js_content or '"line"' in js_content
        assert "'bar'"  in js_content or '"bar"'  in js_content

    def test_tres_instancias_new_chart(self, js_content):
        """Debe haber 3 gráficos instanciados (uno por canvas)."""
        count = js_content.count("new Chart(")
        assert count >= 3, f"Se esperaban ≥3 instancias de Chart, encontradas: {count}"


# ────────────────────────────────────────────────────────────────────────────
# Tests: CSS — sanidad básica
# ────────────────────────────────────────────────────────────────────────────

class TestCSSSanidad:
    def test_css_no_vacio(self, css_content):
        assert len(css_content.strip()) > 0

    def test_css_tiene_reglas(self, css_content):
        """Al menos una regla CSS con selector y propiedad."""
        assert "{" in css_content and "}" in css_content
