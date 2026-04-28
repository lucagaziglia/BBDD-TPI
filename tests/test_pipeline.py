"""
test_pipeline.py — Tests de integración del pipeline ETL completo.

Cubre:
  - Flujo feliz: Extract → Transform → Load retorna resultados con filas
  - Sin datos de MongoDB: pipeline aborta antes del Transform
  - Transform vacío: pipeline aborta antes del Load
  - Estructura del dict de resultados
  - Integración con datos mock (sin dependencias externas)
"""
import sys
import os
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

ROOT = os.path.dirname(os.path.dirname(__file__))
ETL_DIR = os.path.join(ROOT, "etl")
sys.path.insert(0, ROOT)
sys.path.insert(0, ETL_DIR)

from etl.pipeline import run_pipeline


class TestRunPipelineEstructuraResultados:
    """El dict retornado siempre tiene las tres claves esperadas."""

    def test_claves_en_resultado(self, monkeypatch):
        monkeypatch.delenv("MONGODB_URI", raising=False)
        monkeypatch.delenv("REDIS_URL",   raising=False)
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)

        # Mock del loader para no tocar Supabase
        with patch("etl.pipeline.load_to_staging", return_value=2):
            resultado = run_pipeline(dias=1)

        claves_esperadas = {"filas_extraidas", "filas_transformadas", "filas_cargadas"}
        assert claves_esperadas == set(resultado.keys())

    def test_valores_son_enteros(self, monkeypatch):
        monkeypatch.delenv("MONGODB_URI", raising=False)
        monkeypatch.delenv("REDIS_URL",   raising=False)
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)

        with patch("etl.pipeline.load_to_staging", return_value=2):
            resultado = run_pipeline(dias=1)

        for clave, valor in resultado.items():
            assert isinstance(valor, int), f"{clave} no es int: {type(valor)}"


class TestRunPipelineSinDatosMongoDB:
    """Si extract_sensor_readings retorna [], el pipeline aborta sin cargar."""

    def test_aborta_con_cero_extraidos(self, monkeypatch):
        monkeypatch.delenv("MONGODB_URI", raising=False)
        monkeypatch.delenv("REDIS_URL",   raising=False)
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)

        with patch("etl.pipeline.extract_sensor_readings", return_value=[]), \
             patch("etl.pipeline.extract_realtime_state",  return_value={}), \
             patch("etl.pipeline.load_to_staging") as mock_load:

            resultado = run_pipeline(dias=1)

        assert resultado["filas_extraidas"] == 0
        # El loader NO debe ser llamado
        mock_load.assert_not_called()

    def test_filas_transformadas_cero_cuando_no_hay_datos(self, monkeypatch):
        monkeypatch.delenv("MONGODB_URI", raising=False)
        monkeypatch.delenv("REDIS_URL",   raising=False)

        with patch("etl.pipeline.extract_sensor_readings", return_value=[]), \
             patch("etl.pipeline.extract_realtime_state",  return_value={}), \
             patch("etl.pipeline.load_to_staging"):

            resultado = run_pipeline(dias=1)

        assert resultado["filas_transformadas"] == 0
        assert resultado["filas_cargadas"] == 0


class TestRunPipelineTransformVacio:
    """Si transform retorna DF vacío, no se llama al loader."""

    def test_aborta_si_transform_vacio(self, monkeypatch, raw_readings_validos):
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)

        with patch("etl.pipeline.extract_sensor_readings", return_value=raw_readings_validos), \
             patch("etl.pipeline.extract_realtime_state",  return_value={}), \
             patch("etl.pipeline.transform_readings",      return_value=pd.DataFrame()), \
             patch("etl.pipeline.load_to_staging") as mock_load:

            resultado = run_pipeline(dias=1)

        mock_load.assert_not_called()
        assert resultado["filas_cargadas"] == 0


class TestRunPipelineFlujoCorrecto:
    """Pipeline completo con mocks: verifica el flujo Extract→Transform→Load."""

    def test_flujo_completo_mock(self, monkeypatch, raw_readings_validos, lote_localidad_map):
        monkeypatch.delenv("MONGODB_URI", raising=False)
        monkeypatch.delenv("REDIS_URL",   raising=False)
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)

        # DataFrame de salida del transformer (simulado)
        df_mock = pd.DataFrame([{
            "localidad_id": 10, "fecha": "2024-11-03",
            "temp_promedio": 21.5, "temp_max": 22.0,
            "temp_min": 18.0, "humedad_promedio": 62.0,
        }])

        with patch("etl.pipeline.extract_sensor_readings", return_value=raw_readings_validos) as mock_ext, \
             patch("etl.pipeline.extract_realtime_state",  return_value={}) as mock_redis, \
             patch("etl.pipeline.transform_readings",      return_value=df_mock) as mock_tr, \
             patch("etl.pipeline.load_to_staging",         return_value=1) as mock_load, \
             patch("etl.pipeline.fetch_lote_localidad_map", return_value=lote_localidad_map):

            resultado = run_pipeline(dias=7)

        # Verificar que cada paso fue llamado exactamente una vez
        mock_ext.assert_called_once()
        mock_redis.assert_called_once()
        mock_tr.assert_called_once()
        mock_load.assert_called_once()

        assert resultado["filas_extraidas"]    == len(raw_readings_validos)
        assert resultado["filas_transformadas"] == 1
        assert resultado["filas_cargadas"]      == 1

    def test_transformer_recibe_datos_de_extractor(self, monkeypatch, raw_readings_validos):
        """transform_readings recibe exactamente lo que devuelve extract_sensor_readings."""
        monkeypatch.delenv("MONGODB_URI", raising=False)
        monkeypatch.delenv("REDIS_URL",   raising=False)
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)

        df_mock = pd.DataFrame([{
            "localidad_id": 1, "fecha": "2024-11-03",
            "temp_promedio": 20.0, "temp_max": 22.0,
            "temp_min": 18.0, "humedad_promedio": 60.0,
        }])

        with patch("etl.pipeline.extract_sensor_readings", return_value=raw_readings_validos), \
             patch("etl.pipeline.extract_realtime_state",  return_value={}), \
             patch("etl.pipeline.transform_readings",      return_value=df_mock) as mock_tr, \
             patch("etl.pipeline.load_to_staging",         return_value=1), \
             patch("etl.pipeline.fetch_lote_localidad_map", return_value={}):

            run_pipeline(dias=1)

        # El primer argumento de transform_readings debe ser raw_readings_validos
        args, _ = mock_tr.call_args
        assert args[0] == raw_readings_validos


class TestRunPipelineParametroDias:
    """El parámetro `dias` afecta el rango temporal enviado al extractor."""

    def test_parametro_dias_default_es_30(self, monkeypatch):
        """El valor por defecto de `dias` es 30."""
        monkeypatch.delenv("MONGODB_URI", raising=False)
        monkeypatch.delenv("REDIS_URL",   raising=False)

        import inspect
        from etl.pipeline import run_pipeline as rp
        sig = inspect.signature(rp)
        assert sig.parameters["dias"].default == 30
