"""
test_cassandra_extractor.py — Tests del extractor unificado de Cassandra.

Cubre el reemplazo de los viejos extractores Mongo + Redis. Verifica:
  - Fallback a datos mock cuando no hay Cassandra ni Astra configurados
  - Estructura de las lecturas históricas (sensor_readings)
  - Estructura del estado real-time (sensor_realtime + riego_estado)
  - Comportamiento de la conexión cuando faltan credenciales
  - Comportamiento ante error de query (no propaga excepción)
  - Lógica de extracción cuando Cassandra está disponible (mockeada)
"""
import os
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

# Path fix — añade etl/ al path para importar extractors directamente
ETL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "etl")
sys.path.insert(0, ETL_DIR)

from extractors.cassandra_extractor import (
    extract_sensor_readings,
    extract_realtime_state,
    connect_cassandra,
    MOCK_READINGS,
    MOCK_STATE,
)


# ────────────────────────────────────────────────────────────────────────────
# Connect helper
# ────────────────────────────────────────────────────────────────────────────

class TestConnectCassandra:
    """Verifica el factory de conexión y sus paths de fallback."""

    def test_sin_configuracion_retorna_none(self, monkeypatch):
        """Sin CASSANDRA_HOSTS ni ASTRA_DB_SECURE_BUNDLE_PATH retorna None."""
        monkeypatch.delenv("CASSANDRA_HOSTS", raising=False)
        monkeypatch.delenv("ASTRA_DB_SECURE_BUNDLE_PATH", raising=False)
        assert connect_cassandra() is None

    def test_astra_sin_credenciales_retorna_none(self, monkeypatch):
        """ASTRA_DB_SECURE_BUNDLE_PATH definido pero sin CLIENT_ID/SECRET → None."""
        monkeypatch.setenv("ASTRA_DB_SECURE_BUNDLE_PATH", "/fake/bundle.zip")
        monkeypatch.delenv("ASTRA_DB_CLIENT_ID", raising=False)
        monkeypatch.delenv("ASTRA_DB_CLIENT_SECRET", raising=False)
        assert connect_cassandra() is None

    def test_cassandra_local_conexion_fallida_retorna_none(self, monkeypatch):
        """Si Cassandra local no es alcanzable, retorna None (no propaga)."""
        monkeypatch.setenv("CASSANDRA_HOSTS", "127.0.0.1")
        monkeypatch.delenv("ASTRA_DB_SECURE_BUNDLE_PATH", raising=False)

        with patch("cassandra.cluster.Cluster") as mock_cluster:
            mock_cluster.side_effect = Exception("Connection refused")
            assert connect_cassandra() is None


# ────────────────────────────────────────────────────────────────────────────
# extract_sensor_readings — modo mock
# ────────────────────────────────────────────────────────────────────────────

class TestExtractSensorReadingsMock:
    """Cuando no hay session, devuelve MOCK_READINGS filtradas por fecha."""

    def test_sin_session_devuelve_mock(self, monkeypatch):
        monkeypatch.delenv("CASSANDRA_HOSTS", raising=False)
        monkeypatch.delenv("ASTRA_DB_SECURE_BUNDLE_PATH", raising=False)

        resultado = extract_sensor_readings(
            desde=datetime(2020, 1, 1),
            hasta=datetime(2030, 12, 31),
        )
        assert resultado == MOCK_READINGS

    def test_filtra_por_rango_de_fechas(self, monkeypatch):
        """El rango de fechas filtra los mock docs correctamente."""
        monkeypatch.delenv("CASSANDRA_HOSTS", raising=False)

        resultado = extract_sensor_readings(
            desde=datetime(2020, 1, 1),
            hasta=datetime(2020, 1, 2),
        )
        # Ningún mock cae en ese rango → lista vacía
        assert resultado == []

    def test_mock_no_vacio(self):
        assert len(MOCK_READINGS) > 0

    def test_mock_estructura_documentos(self):
        """Cada doc mock tiene los campos esperados por el transformer."""
        campos_requeridos = {"lote_id", "timestamp", "temp", "humedad_suelo", "precipitacion", "agua"}
        for doc in MOCK_READINGS:
            assert campos_requeridos.issubset(doc.keys()), f"Doc incompleto: {doc}"
            assert isinstance(doc["lote_id"], int)
            assert isinstance(doc["timestamp"], datetime)
            assert isinstance(doc["temp"], (int, float))
            assert isinstance(doc["humedad_suelo"], (int, float))

    def test_mock_valores_en_rango(self):
        """Las métricas mock están en rangos físicamente razonables."""
        for doc in MOCK_READINGS:
            assert 0 <= doc["humedad_suelo"] <= 100, f"Humedad fuera de rango: {doc}"
            assert -30 <= doc["temp"] <= 60,         f"Temp fuera de rango: {doc}"
            assert doc["precipitacion"] >= 0
            assert doc["agua"] >= 0

    def test_mock_lote_ids_validos(self):
        for doc in MOCK_READINGS:
            assert 1 <= doc["lote_id"] <= 25


# ────────────────────────────────────────────────────────────────────────────
# extract_sensor_readings — con session mockeada
# ────────────────────────────────────────────────────────────────────────────

class TestExtractSensorReadingsConSession:
    """Con una session mockeada, traduce filas Cassandra a dicts."""

    def test_traduce_filas_a_dicts(self):
        """Cada Row de Cassandra se convierte en un dict con los campos esperados."""
        session = MagicMock()

        # Una fila mockeada por lote (25 lotes × 1 fila = 25 docs)
        def execute_side_effect(stmt, params=None):
            if params is None:
                return []
            lote_id, _, _ = params
            row = MagicMock()
            row.lote_id       = lote_id
            row.timestamp     = datetime(2025, 6, 28, 12, 0)
            row.temp          = 22.5
            row.humedad_suelo = 60.0
            row.precipitacion = 0.0
            row.agua          = 30.0
            return [row]

        session.execute.side_effect = execute_side_effect
        session.prepare.return_value = "PREPARED_STMT"

        resultado = extract_sensor_readings(
            desde=datetime(2025, 6, 1),
            hasta=datetime(2025, 7, 1),
            session=session,
        )

        # 25 lotes × 1 fila cada uno
        assert len(resultado) == 25
        for doc in resultado:
            assert set(doc.keys()) == {
                "lote_id", "timestamp", "temp",
                "humedad_suelo", "precipitacion", "agua",
            }

    def test_query_usa_prepared_statement(self):
        """El extractor usa PreparedStatement para evitar recompilar la query."""
        session = MagicMock()
        session.execute.return_value = []
        session.prepare.return_value = "PREPARED_STMT"

        extract_sensor_readings(
            desde=datetime(2025, 6, 1),
            hasta=datetime(2025, 7, 1),
            session=session,
        )
        session.prepare.assert_called_once()
        # Una query por cada uno de los 25 lotes
        assert session.execute.call_count == 25

    def test_retorna_mock_en_error_de_query(self):
        """Si la session lanza al preparar, cae a mock filtrado."""
        session = MagicMock()
        session.prepare.side_effect = Exception("Schema not found")

        resultado = extract_sensor_readings(
            desde=datetime(2020, 1, 1),
            hasta=datetime(2030, 12, 31),
            session=session,
        )
        # Fallback a MOCK_READINGS (rango muy amplio = todos los mocks)
        assert resultado == MOCK_READINGS


# ────────────────────────────────────────────────────────────────────────────
# extract_realtime_state — modo mock
# ────────────────────────────────────────────────────────────────────────────

class TestExtractRealtimeStateMock:
    """Sin session, retorna MOCK_STATE."""

    def test_sin_session_devuelve_mock(self, monkeypatch):
        monkeypatch.delenv("CASSANDRA_HOSTS", raising=False)
        monkeypatch.delenv("ASTRA_DB_SECURE_BUNDLE_PATH", raising=False)
        resultado = extract_realtime_state()
        assert resultado == MOCK_STATE

    def test_mock_no_vacio(self):
        assert len(MOCK_STATE) > 0

    def test_mock_contiene_sensores(self):
        humedades    = [k for k in MOCK_STATE if ":humedad" in k]
        temperaturas = [k for k in MOCK_STATE if ":temperatura" in k]
        assert len(humedades)    > 0
        assert len(temperaturas) > 0

    def test_mock_contiene_riego(self):
        riegos = [k for k in MOCK_STATE if k.startswith("riego:")]
        assert len(riegos) > 0

    def test_mock_estado_riego_validos(self):
        for key, val in MOCK_STATE.items():
            if key.startswith("riego:"):
                assert val in ("ON", "OFF"), f"Estado inválido en {key}: {val}"

    def test_mock_valores_numericos_parseables(self):
        for key, val in MOCK_STATE.items():
            if key.startswith("sensor:"):
                try:
                    float(val)
                except (ValueError, TypeError):
                    pytest.fail(f"Valor no parseable en {key}: {val!r}")

    def test_mock_estructura_keys(self):
        """Todas las keys siguen sensor:{id}:tipo o riego:{id}:estado."""
        for key in MOCK_STATE:
            partes = key.split(":")
            assert len(partes) == 3, f"Formato inesperado: {key}"
            assert partes[0] in ("sensor", "riego")
            assert partes[1].isdigit()


# ────────────────────────────────────────────────────────────────────────────
# extract_realtime_state — con session mockeada
# ────────────────────────────────────────────────────────────────────────────

class TestExtractRealtimeStateConSession:
    """Con session mockeada, aplasta sensor_realtime + riego_estado al dict legacy."""

    def test_aplasta_dos_tablas_en_dict_unico(self):
        session = MagicMock()

        # sensor_realtime: lote_id=1 (humedad+temp), lote_id=2 (humedad+temp)
        sensor_row_1 = MagicMock(); sensor_row_1.lote_id = 1; sensor_row_1.humedad = 62.3; sensor_row_1.temperatura = 21.4
        sensor_row_2 = MagicMock(); sensor_row_2.lote_id = 2; sensor_row_2.humedad = 45.1; sensor_row_2.temperatura = 23.0

        # riego_estado: ON para el 1, OFF para el 2
        riego_row_1 = MagicMock(); riego_row_1.lote_id = 1; riego_row_1.estado = "ON"
        riego_row_2 = MagicMock(); riego_row_2.lote_id = 2; riego_row_2.estado = "OFF"

        def execute_side_effect(query):
            if "sensor_realtime" in query:
                return [sensor_row_1, sensor_row_2]
            if "riego_estado" in query:
                return [riego_row_1, riego_row_2]
            return []

        session.execute.side_effect = execute_side_effect

        resultado = extract_realtime_state(session=session)

        assert resultado["sensor:1:humedad"]     == "62.3"
        assert resultado["sensor:1:temperatura"] == "21.4"
        assert resultado["sensor:2:humedad"]     == "45.1"
        assert resultado["riego:1:estado"]       == "ON"
        assert resultado["riego:2:estado"]       == "OFF"

    def test_ignora_valores_nulos(self):
        """Si una columna viene en NULL, no se incluye en el dict."""
        session = MagicMock()

        sensor_row = MagicMock(); sensor_row.lote_id = 1; sensor_row.humedad = None; sensor_row.temperatura = 21.4

        def execute_side_effect(query):
            if "sensor_realtime" in query:
                return [sensor_row]
            return []

        session.execute.side_effect = execute_side_effect

        resultado = extract_realtime_state(session=session)

        assert "sensor:1:humedad" not in resultado
        assert resultado["sensor:1:temperatura"] == "21.4"

    def test_retorna_vacio_en_error(self):
        """Si la query falla, retorna dict vacío sin propagar la excepción."""
        session = MagicMock()
        session.execute.side_effect = Exception("Cluster down")
        resultado = extract_realtime_state(session=session)
        assert resultado == {}
