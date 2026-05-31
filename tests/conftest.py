"""
conftest.py — Fixtures compartidas para toda la suite de tests.

Disponibles en todos los módulos de tests sin necesidad de importar.
"""
import os
import sys
from datetime import datetime

import pytest

# Agrega la raíz del repo y el directorio etl/ al sys.path
ROOT = os.path.dirname(os.path.dirname(__file__))
ETL_DIR = os.path.join(ROOT, "etl")
sys.path.insert(0, ROOT)
sys.path.insert(0, ETL_DIR)


# ────────────────────────────────────────────────────────────────────────────
# Fixtures: datos crudos de Cassandra para las pruebas
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def raw_readings_validos():
    """
    Lecturas crudas con la misma estructura que devuelve `cassandra_extractor`
    """
    return [
        {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8,  0),
         "temp": 21.4, "humedad_suelo": 62.3, "precipitacion": 0.0, "agua": 15.0},
        {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 9,  0),
         "temp": 21.6, "humedad_suelo": 61.8, "precipitacion": 0.0, "agua": 18.0},
        {"lote_id": 2, "timestamp": datetime(2024, 11, 3, 8,  0),
         "temp": 23.0, "humedad_suelo": 45.1, "precipitacion": 0.0, "agua": 22.0},
        {"lote_id": 2, "timestamp": datetime(2024, 11, 3, 9,  0),
         "temp": 23.2, "humedad_suelo": 46.0, "precipitacion": 2.5, "agua": 20.0},
    ]


@pytest.fixture
def lote_localidad_map():
    """Mapeo lote_id → localidad_id de ejemplo (quedo de antes, usado por algunos tests)."""
    return {1: 10, 2: 11, 3: 12}


@pytest.fixture
def mock_realtime_state():
    """Snapshot del estado caliente, equivalente al MOCK_STATE del extractor."""
    return {
        "sensor:1:humedad":     "62.3",
        "sensor:1:temperatura": "21.4",
        "sensor:2:humedad":     "45.1",
        "sensor:2:temperatura": "23.0",
        "riego:1:estado":       "ON",
        "riego:2:estado":       "OFF",
    }
