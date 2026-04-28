"""
conftest.py — Fixtures compartidas para toda la suite de tests.

Disponibles en todos los módulos de tests sin necesidad de importar.
"""
import sys
import os
import pytest
import pandas as pd
from datetime import datetime

# ── Path fix: permite importar los módulos del proyecto ──────────────────────
# Agrega la raíz del repo y el directorio etl/ al sys.path
ROOT = os.path.dirname(os.path.dirname(__file__))
ETL_DIR = os.path.join(ROOT, "etl")
sys.path.insert(0, ROOT)
sys.path.insert(0, ETL_DIR)


# ────────────────────────────────────────────────────────────────────────────
# Fixtures: datos crudos de MongoDB (mock)
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def raw_readings_validos():
    """Lecturas crudas dentro de rangos válidos (el transformer NO las descarta)."""
    return [
        {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8,  0), "tipo_lectura": "HUMEDAD_SUELO", "valor": 62.3},
        {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 15), "tipo_lectura": "HUMEDAD_SUELO", "valor": 61.8},
        {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8,  0), "tipo_lectura": "TEMPERATURA",   "valor": 21.4},
        {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 15), "tipo_lectura": "TEMPERATURA",   "valor": 21.6},
        {"lote_id": 2, "timestamp": datetime(2024, 11, 3, 8,  0), "tipo_lectura": "HUMEDAD_SUELO", "valor": 45.1},
        {"lote_id": 2, "timestamp": datetime(2024, 11, 3, 8,  0), "tipo_lectura": "TEMPERATURA",   "valor": 23.0},
    ]


@pytest.fixture
def raw_readings_con_outliers(raw_readings_validos):
    """Lecturas que mezclan valores válidos con outliers extremos."""
    return raw_readings_validos + [
        # Humedad imposible (> 100 y < 10)
        {"lote_id": 3, "timestamp": datetime(2024, 11, 3, 8, 0), "tipo_lectura": "HUMEDAD_SUELO", "valor": 150.0},
        {"lote_id": 3, "timestamp": datetime(2024, 11, 3, 8, 0), "tipo_lectura": "HUMEDAD_SUELO", "valor": 5.0},
        # Temperatura imposible (> 50 y < -10)
        {"lote_id": 3, "timestamp": datetime(2024, 11, 3, 8, 0), "tipo_lectura": "TEMPERATURA",   "valor": 80.0},
        {"lote_id": 3, "timestamp": datetime(2024, 11, 3, 8, 0), "tipo_lectura": "TEMPERATURA",   "valor": -25.0},
    ]


@pytest.fixture
def lote_localidad_map():
    """Mapeo lote_id → localidad_id de ejemplo."""
    return {1: 10, 2: 11, 3: 12}


@pytest.fixture
def df_transformado(raw_readings_validos, lote_localidad_map):
    """DataFrame ya transformado listo para cargar."""
    from transformers.sensor_transformer import transform_readings
    return transform_readings(raw_readings_validos, lote_localidad_map=lote_localidad_map)


@pytest.fixture
def mock_redis_state():
    """Estado Redis completo (mock de MOCK_STATE en redis_extractor)."""
    return {
        "sensor:1:humedad":     "62.3",
        "sensor:1:temperatura": "21.4",
        "sensor:2:humedad":     "45.1",
        "sensor:2:temperatura": "23.0",
        "riego:1:estado":       "ON",
        "riego:2:estado":       "OFF",
    }
