"""
test_sensor_transformer.py — Tests del transformador de lecturas.

Cubre:
  - Columnas de salida obligatorias
  - Filtrado de outliers por tipo de lectura
  - Mapeo lote_id → localidad_id
  - Fallback cuando no hay mapa (usa lote_id como localidad_id)
  - Agregación diaria correcta (promedio, max, min)
  - DataFrame vacío en entrada → DataFrame vacío en salida
  - Lecturas sin mapeo se descartan (no crashean)
"""
import sys
import os
import pytest
import pandas as pd
from datetime import datetime

ETL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "etl")
sys.path.insert(0, ETL_DIR)

from transformers.sensor_transformer import transform_readings, RANGOS_VALIDOS


class TestTransformReadingsColumnas:
    """Verifica que el DataFrame de salida tenga las columnas correctas."""

    COLUMNAS_ESPERADAS = {
        "localidad_id", "fecha",
        "temp_promedio", "temp_max", "temp_min",
        "humedad_promedio",
    }

    def test_columnas_presentes(self, raw_readings_validos, lote_localidad_map):
        df = transform_readings(raw_readings_validos, lote_localidad_map=lote_localidad_map)
        assert not df.empty
        for col in self.COLUMNAS_ESPERADAS:
            assert col in df.columns, f"Columna faltante: {col}"

    def test_tipos_de_datos(self, raw_readings_validos, lote_localidad_map):
        df = transform_readings(raw_readings_validos, lote_localidad_map=lote_localidad_map)
        assert pd.api.types.is_integer_dtype(df["localidad_id"])
        # fecha puede ser date o string — verificar que sea parseable
        assert df["fecha"].notna().all()


class TestTransformReadingsEntradaVacia:
    """Cuando la entrada está vacía, el resultado debe ser un DataFrame vacío."""

    def test_lista_vacia_retorna_dataframe_vacio(self):
        df = transform_readings([])
        assert isinstance(df, pd.DataFrame)
        assert df.empty


class TestTransformReadingsFiltradoOutliers:
    """Verifica que los outliers se filtran según RANGOS_VALIDOS."""

    def test_descarta_humedad_sobre_100(self, lote_localidad_map):
        # El transformer necesita TEMPERATURA para completar el pivot;
        # incluimos una lectura de temperatura válida.
        readings = [
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "HUMEDAD_SUELO", "valor": 150.0},  # outlier
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "HUMEDAD_SUELO", "valor": 60.0},   # válido
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "TEMPERATURA",   "valor": 20.0},   # necesario para pivot
        ]
        df = transform_readings(readings, lote_localidad_map=lote_localidad_map)
        # Solo queda la humedad válida; promedio debe ser ≈ 60, no 105
        assert not df.empty
        assert df["humedad_promedio"].iloc[0] == pytest.approx(60.0, abs=0.1)

    def test_descarta_humedad_bajo_10(self, lote_localidad_map):
        readings = [
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "HUMEDAD_SUELO", "valor": 5.0},    # outlier
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "HUMEDAD_SUELO", "valor": 55.0},   # válido
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "TEMPERATURA",   "valor": 20.0},   # necesario para pivot
        ]
        df = transform_readings(readings, lote_localidad_map=lote_localidad_map)
        assert not df.empty
        assert df["humedad_promedio"].iloc[0] == pytest.approx(55.0, abs=0.1)

    def test_descarta_temperatura_sobre_50(self, lote_localidad_map):
        readings = [
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "TEMPERATURA", "valor": 80.0},   # outlier
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "TEMPERATURA", "valor": 22.0},   # válido
        ]
        df = transform_readings(readings, lote_localidad_map=lote_localidad_map)
        assert not df.empty
        assert df["temp_promedio"].iloc[0] == pytest.approx(22.0, abs=0.1)

    def test_descarta_temperatura_bajo_menos_10(self, lote_localidad_map):
        readings = [
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "TEMPERATURA", "valor": -25.0},  # outlier
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "TEMPERATURA", "valor": 18.0},   # válido
        ]
        df = transform_readings(readings, lote_localidad_map=lote_localidad_map)
        assert not df.empty
        assert df["temp_promedio"].iloc[0] == pytest.approx(18.0, abs=0.1)

    def test_todos_outliers_retorna_vacio(self):
        """Si todas las lecturas son outliers, transform retorna DataFrame vacío."""
        readings = [
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "HUMEDAD_SUELO", "valor": 999.0},
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "TEMPERATURA",   "valor": -99.0},
        ]
        # Todos los outliers son filtrados → el DataFrame antes del pivot queda vacío
        # El transformer retorna DF vacío sin llegar al pivot
        df = transform_readings(readings, lote_localidad_map=None)
        assert df.empty

    def test_rangos_definidos_para_tipos_conocidos(self):
        """RANGOS_VALIDOS tiene entradas para HUMEDAD_SUELO y TEMPERATURA."""
        assert "HUMEDAD_SUELO" in RANGOS_VALIDOS
        assert "TEMPERATURA"   in RANGOS_VALIDOS
        h_min, h_max = RANGOS_VALIDOS["HUMEDAD_SUELO"]
        t_min, t_max = RANGOS_VALIDOS["TEMPERATURA"]
        assert h_min < h_max
        assert t_min < t_max


class TestTransformReadingsMapeoLocalidad:
    """Verifica el mapeo lote_id → localidad_id."""

    def test_con_mapa_usa_localidad_correcta(self, raw_readings_validos, lote_localidad_map):
        df = transform_readings(raw_readings_validos, lote_localidad_map=lote_localidad_map)
        localidades_resultado = set(df["localidad_id"].unique())
        localidades_esperadas = set(lote_localidad_map.values())
        # Las localidades en el resultado deben ser un subconjunto de las esperadas
        assert localidades_resultado.issubset(localidades_esperadas)

    def test_sin_mapa_usa_lote_id(self):
        readings = [
            {"lote_id": 7, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "HUMEDAD_SUELO", "valor": 60.0},
            {"lote_id": 7, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "TEMPERATURA",   "valor": 20.0},
        ]
        df = transform_readings(readings, lote_localidad_map=None)
        assert not df.empty
        # Sin mapa: localidad_id == lote_id
        assert 7 in df["localidad_id"].values

    def test_lecturas_sin_mapeo_se_descartan(self):
        """Lotes que no están en lote_localidad_map se eliminan silenciosamente."""
        readings = [
            # lote 99 no está en el mapa
            {"lote_id": 99, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "HUMEDAD_SUELO", "valor": 60.0},
            # lote 1 sí está
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "HUMEDAD_SUELO", "valor": 55.0},
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "TEMPERATURA",   "valor": 20.0},
        ]
        mapa = {1: 10}
        df = transform_readings(readings, lote_localidad_map=mapa)
        assert not df.empty
        # No debe aparecer lote 99
        assert 99 not in df["localidad_id"].values


class TestTransformReadingsAgregacion:
    """Verifica que la agregación diaria sea correcta."""

    def test_promedio_humedad_correcto(self, lote_localidad_map):
        readings = [
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8,  0),
             "tipo_lectura": "HUMEDAD_SUELO", "valor": 60.0},
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 15),
             "tipo_lectura": "HUMEDAD_SUELO", "valor": 80.0},
            # Temperatura requerida para que el pivot de temp_max/temp_min funcione
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8,  0),
             "tipo_lectura": "TEMPERATURA",   "valor": 20.0},
        ]
        df = transform_readings(readings, lote_localidad_map=lote_localidad_map)
        # Promedio de 60 y 80 = 70
        assert df["humedad_promedio"].iloc[0] == pytest.approx(70.0, abs=0.01)

    def test_max_temperatura_correcto(self, lote_localidad_map):
        readings = [
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8,  0),
             "tipo_lectura": "TEMPERATURA", "valor": 18.0},
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 15),
             "tipo_lectura": "TEMPERATURA", "valor": 26.0},
        ]
        df = transform_readings(readings, lote_localidad_map=lote_localidad_map)
        assert df["temp_max"].iloc[0] == pytest.approx(26.0, abs=0.01)

    def test_min_temperatura_correcto(self, lote_localidad_map):
        readings = [
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8,  0),
             "tipo_lectura": "TEMPERATURA", "valor": 18.0},
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 15),
             "tipo_lectura": "TEMPERATURA", "valor": 26.0},
        ]
        df = transform_readings(readings, lote_localidad_map=lote_localidad_map)
        assert df["temp_min"].iloc[0] == pytest.approx(18.0, abs=0.01)

    def test_agrega_por_dia_no_por_lectura(self, lote_localidad_map):
        """Varias lecturas del mismo día → 1 sola fila en el resultado."""
        readings = [
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8,  0),
             "tipo_lectura": "HUMEDAD_SUELO", "valor": 60.0},
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 10, 0),
             "tipo_lectura": "HUMEDAD_SUELO", "valor": 65.0},
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8,  0),
             "tipo_lectura": "TEMPERATURA",   "valor": 20.0},
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 10, 0),
             "tipo_lectura": "TEMPERATURA",   "valor": 22.0},
        ]
        df = transform_readings(readings, lote_localidad_map=lote_localidad_map)
        # Solo debe haber 1 fila (lote 1, día 2024-11-03)
        assert len(df) == 1

    def test_dias_distintos_generan_filas_distintas(self, lote_localidad_map):
        """Lecturas de días distintos → una fila por día."""
        readings = [
            # Día 1
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "HUMEDAD_SUELO", "valor": 60.0},
            {"lote_id": 1, "timestamp": datetime(2024, 11, 3, 8, 0),
             "tipo_lectura": "TEMPERATURA",   "valor": 20.0},
            # Día 2
            {"lote_id": 1, "timestamp": datetime(2024, 11, 4, 8, 0),
             "tipo_lectura": "HUMEDAD_SUELO", "valor": 55.0},
            {"lote_id": 1, "timestamp": datetime(2024, 11, 4, 8, 0),
             "tipo_lectura": "TEMPERATURA",   "valor": 21.0},
        ]
        df = transform_readings(readings, lote_localidad_map=lote_localidad_map)
        assert len(df) == 2
