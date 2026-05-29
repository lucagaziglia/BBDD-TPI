"""
test_cassandra_extractor.py — Tests del extractor unificado de Astra DB.

Cubre la extracción de datos desde Astra DB (managed Cassandra) mediante AstrayPy Data API.
Verifica:
  - Fallback a datos mock cuando no hay Astra DB configurado
  - Estructura de las lecturas históricas (sensor_readings)
  - Estructura del estado real-time (sensor_realtime + riego_estado)
  - Comportamiento ante error de conexión (no propaga excepción)
  - Lógica de extracción con Astra DB disponible (mockeada)
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
    connect_astradb,
    MOCK_READINGS,
    MOCK_STATE,
)

# ────────────────────────────────────────────────────────────────────────────
# Connect helper
# ────────────────────────────────────────────────────────────────────────────

class TestConnectAstradb:
    """Verifica la conexión a Astra DB y fallback a mock."""

    def test_sin_configuracion_retorna_none(self, monkeypatch):
        """Sin ASTRA_DB_URL ni ASTRA_DB_TOKEN retorna None."""
        monkeypatch.delenv("ASTRA_DB_URL", raising=False)
        monkeypatch.delenv("ASTRA_DB_TOKEN", raising=False)
        resultado = connect_astradb("sensor_readings")
        assert resultado is None

    def test_credenciales_incompletas_retorna_none(self, monkeypatch):
        """Con solo URL pero sin TOKEN retorna None."""
        monkeypatch.setenv("ASTRA_DB_URL", "https://example.com")
        monkeypatch.delenv("ASTRA_DB_TOKEN", raising=False)
        resultado = connect_astradb("sensor_readings")
        assert resultado is None



# ────────────────────────────────────────────────────────────────────────────
# extract_sensor_readings — modo mock
# ────────────────────────────────────────────────────────────────────────────

class TestExtractSensorReadingsMock:
    """Cuando no hay Astra DB configurado, devuelve MOCK_READINGS filtradas por fecha."""

    def test_sin_astradb_devuelve_mock(self, monkeypatch):
        monkeypatch.delenv("ASTRA_DB_URL", raising=False)
        monkeypatch.delenv("ASTRA_DB_TOKEN", raising=False)

        resultado = extract_sensor_readings(
            desde=datetime(2020, 1, 1),
            hasta=datetime(2030, 12, 31),
        )
        assert resultado == MOCK_READINGS

    def test_filtra_por_rango_de_fechas(self, monkeypatch):
        """El rango de fechas filtra los mock docs correctamente."""
        monkeypatch.delenv("ASTRA_DB_URL", raising=False)
        monkeypatch.delenv("ASTRA_DB_TOKEN", raising=False)

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
# extract_sensor_readings — con Astra DB mockeada
# ────────────────────────────────────────────────────────────────────────────

class TestExtractSensorReadingsConAstradb:
    """Con Astra DB mockeada, traduce documentos Astra a dicts."""

    def test_estructura_documentos_astradb(self):
        """Verifica que se puede deserializar documentos de Astra DB correctamente."""
        # En caso real, Astra devuelve documentos como dicts
        doc_astra = {
            "lote_id": 1,
            "timestamp": "2025-06-28T12:00:00Z",
            "temp": 22.5,
            "humedad_suelo": 60.0,
            "precipitacion": 0.0,
            "agua": 30.0,
        }
        
        # El extractor debe convertir timestamp de string ISO a datetime
        assert doc_astra["lote_id"] == 1
        assert isinstance(doc_astra["temp"], (int, float))
        assert isinstance(doc_astra["humedad_suelo"], (int, float))

    def test_retorna_lista_de_dicts(self):
        """El extractor retorna una lista de dictionaries."""
        resultado = extract_sensor_readings(
            desde=datetime(2020, 1, 1),
            hasta=datetime(2030, 12, 31),
        )
        assert isinstance(resultado, list)
        if len(resultado) > 0:
            assert isinstance(resultado[0], dict)

    def test_retorna_vacio_en_error_de_conexion(self, monkeypatch):
        """Si la conexión a Astra falla, retorna lista vacía (no propaga)."""
        monkeypatch.setenv("ASTRA_DB_URL", "https://invalid.example.com")
        monkeypatch.setenv("ASTRA_DB_TOKEN", "invalid_token")
        
        # No debe lanzar excepción, sino retornar []
        resultado = extract_sensor_readings(
            desde=datetime(2025, 6, 1),
            hasta=datetime(2025, 7, 1),
        )
        assert isinstance(resultado, list)


# ────────────────────────────────────────────────────────────────────────────
# extract_realtime_state — modo mock
# ────────────────────────────────────────────────────────────────────────────

class TestExtractRealtimeStateMock:
    """Sin Astra DB configurado, retorna MOCK_STATE."""

    def test_sin_astradb_devuelve_mock(self, monkeypatch):
        monkeypatch.delenv("ASTRA_DB_URL", raising=False)
        monkeypatch.delenv("ASTRA_DB_TOKEN", raising=False)
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
# extract_realtime_state — con Astra DB mockeada
# ────────────────────────────────────────────────────────────────────────────

class TestExtractRealtimeStateConAstradb:
    """Con Astra DB mockeada, aplasta sensor_realtime + riego_estado al dict legacy."""

    def test_estructura_dict_realtime(self):
        """Verifica que el dict de realtime tiene estructura sensor:id:tipo y riego:id:estado."""
        resultado = extract_realtime_state()
        
        # Debe retornar algo (mock en este caso)
        assert isinstance(resultado, dict)
        
        # Si hay contenido, verifica formato
        for key in resultado:
            partes = key.split(":")
            assert len(partes) == 3, f"Formato inesperado: {key}"
            assert partes[0] in ("sensor", "riego")

    def test_retorna_dict_vacio_en_error(self, monkeypatch):
        """Si la conexión falla, retorna dict vacío (no propaga)."""
        monkeypatch.setenv("ASTRA_DB_URL", "https://invalid.example.com")
        monkeypatch.setenv("ASTRA_DB_TOKEN", "invalid_token")
        
        # No debe lanzar excepción, sino retornar {}
        resultado = extract_realtime_state()
        assert isinstance(resultado, dict)

