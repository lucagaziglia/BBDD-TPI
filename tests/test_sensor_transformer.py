"""
test_sensor_transformer.py — Tests del transformador de lecturas.

Cubre:
  - DataFrame vacío en entrada → DataFrame vacío en salida
  - Columnas de salida obligatorias (alineadas con `dim_mediciones_diarias`)
  - Mapeo de nombres alternativos (`temp` → `temperatura`, `humedad_suelo` → `humedad`)
  - Filtrado por `lotes_activos`
  - Agregación diaria correcta (promedio, max, min, suma)
  - Dos días distintos → dos filas
"""
import os
import sys
from datetime import datetime

import pandas as pd
import pytest

ETL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "etl")
sys.path.insert(0, ETL_DIR)

from transformers.sensor_transformer import transform_readings


COLUMNAS_ESPERADAS = {
    "lote_id", "fecha", "mes",
    "temp_prom", "temp_max", "temp_min",
    "humedad_prom", "precipitacion_mm", "m3_agua_consumida",
}


def _reading(lote_id: int, ts: datetime, temp: float, humedad: float,
             precip: float = 0.0, agua: float = 0.0) -> dict:
    """Helper: una lectura con la estructura que devuelve cassandra_extractor."""
    return {
        "lote_id":       lote_id,
        "timestamp":     ts,
        "temp":          temp,
        "humedad_suelo": humedad,
        "precipitacion": precip,
        "agua":          agua,
    }


class TestTransformReadingsEntradaVacia:
    """Cuando la entrada está vacía, el resultado debe ser un DataFrame vacío."""

    def test_lista_vacia_retorna_dataframe_vacio(self):
        df = transform_readings([], lotes_activos=set())
        assert isinstance(df, pd.DataFrame)
        assert df.empty


class TestTransformReadingsColumnas:
    """Verifica que el DataFrame de salida tenga las columnas correctas."""

    def test_columnas_presentes(self):
        readings = [
            _reading(1, datetime(2024, 11, 3, 8, 0), 21.4, 62.3, 0.0, 15.0),
            _reading(1, datetime(2024, 11, 3, 9, 0), 21.6, 61.8, 0.0, 18.0),
        ]
        df = transform_readings(readings, lotes_activos={1})
        assert not df.empty
        for col in COLUMNAS_ESPERADAS:
            assert col in df.columns, f"Columna faltante: {col}"

    def test_lote_id_es_entero(self):
        readings = [_reading(1, datetime(2024, 11, 3, 8, 0), 21.4, 62.3)]
        df = transform_readings(readings, lotes_activos={1})
        assert pd.api.types.is_integer_dtype(df["lote_id"])


class TestTransformReadingsNombresAlternativos:
    """El transformer renombra `humedad_suelo` → `humedad` y `temp` → `temperatura`."""

    def test_mapea_humedad_suelo(self):
        readings = [_reading(1, datetime(2024, 11, 3, 8, 0), 22.0, 60.0)]
        df = transform_readings(readings, lotes_activos={1})
        assert df["humedad_prom"].iloc[0] == pytest.approx(60.0, abs=0.01)

    def test_mapea_temp_a_temperatura(self):
        readings = [_reading(1, datetime(2024, 11, 3, 8, 0), 22.0, 60.0)]
        df = transform_readings(readings, lotes_activos={1})
        assert df["temp_prom"].iloc[0] == pytest.approx(22.0, abs=0.01)


class TestTransformReadingsLotesActivos:
    """Lecturas de lotes no activos deben descartarse."""

    def test_filtra_lotes_no_activos(self):
        readings = [
            _reading(1,  datetime(2024, 11, 3, 8, 0), 22.0, 60.0),
            _reading(99, datetime(2024, 11, 3, 8, 0), 22.0, 60.0),  # No activo
        ]
        df = transform_readings(readings, lotes_activos={1})
        assert 99 not in df["lote_id"].values
        assert 1  in df["lote_id"].values


class TestTransformReadingsAgregacion:
    """Verifica que la agregación diaria sea correcta."""

    def test_promedio_humedad_correcto(self):
        readings = [
            _reading(1, datetime(2024, 11, 3, 8,  0), 22.0, 60.0),
            _reading(1, datetime(2024, 11, 3, 9,  0), 22.0, 80.0),
        ]
        df = transform_readings(readings, lotes_activos={1})
        # Promedio de 60 y 80 = 70
        assert df["humedad_prom"].iloc[0] == pytest.approx(70.0, abs=0.01)

    def test_max_temperatura_correcto(self):
        readings = [
            _reading(1, datetime(2024, 11, 3, 8, 0), 18.0, 60.0),
            _reading(1, datetime(2024, 11, 3, 9, 0), 26.0, 60.0),
        ]
        df = transform_readings(readings, lotes_activos={1})
        assert df["temp_max"].iloc[0] == pytest.approx(26.0, abs=0.01)

    def test_min_temperatura_correcto(self):
        readings = [
            _reading(1, datetime(2024, 11, 3, 8, 0), 18.0, 60.0),
            _reading(1, datetime(2024, 11, 3, 9, 0), 26.0, 60.0),
        ]
        df = transform_readings(readings, lotes_activos={1})
        assert df["temp_min"].iloc[0] == pytest.approx(18.0, abs=0.01)

    def test_precipitacion_se_suma(self):
        """precipitacion_mm es la SUMA del día (mm acumulados), no promedio."""
        readings = [
            _reading(1, datetime(2024, 11, 3, 8, 0), 22.0, 60.0, precip=2.0),
            _reading(1, datetime(2024, 11, 3, 9, 0), 22.0, 60.0, precip=3.0),
        ]
        df = transform_readings(readings, lotes_activos={1})
        assert df["precipitacion_mm"].iloc[0] == pytest.approx(5.0, abs=0.01)

    def test_agua_se_suma(self):
        """m3_agua_consumida es la SUMA del día, no promedio."""
        readings = [
            _reading(1, datetime(2024, 11, 3, 8, 0), 22.0, 60.0, agua=10.0),
            _reading(1, datetime(2024, 11, 3, 9, 0), 22.0, 60.0, agua=15.0),
        ]
        df = transform_readings(readings, lotes_activos={1})
        assert df["m3_agua_consumida"].iloc[0] == pytest.approx(25.0, abs=0.01)

    def test_agrega_por_dia_no_por_lectura(self):
        """Varias lecturas del mismo día → 1 sola fila en el resultado."""
        readings = [
            _reading(1, datetime(2024, 11, 3, 8,  0), 22.0, 60.0),
            _reading(1, datetime(2024, 11, 3, 10, 0), 22.0, 65.0),
            _reading(1, datetime(2024, 11, 3, 14, 0), 22.0, 70.0),
        ]
        df = transform_readings(readings, lotes_activos={1})
        assert len(df) == 1

    def test_dias_distintos_generan_filas_distintas(self):
        readings = [
            _reading(1, datetime(2024, 11, 3, 8, 0), 22.0, 60.0),
            _reading(1, datetime(2024, 11, 4, 8, 0), 22.0, 55.0),
        ]
        df = transform_readings(readings, lotes_activos={1})
        assert len(df) == 2

    def test_lotes_distintos_generan_filas_distintas(self):
        readings = [
            _reading(1, datetime(2024, 11, 3, 8, 0), 22.0, 60.0),
            _reading(2, datetime(2024, 11, 3, 8, 0), 23.0, 55.0),
        ]
        df = transform_readings(readings, lotes_activos={1, 2})
        assert len(df) == 2
        assert set(df["lote_id"].values) == {1, 2}
