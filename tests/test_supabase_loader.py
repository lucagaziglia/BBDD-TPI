"""
test_supabase_loader.py — Tests del loader de Supabase.

Cubre:
  - Modo dry-run cuando faltan credenciales (retorna len(df))
  - DataFrame vacío → retorna 0
  - Conversión correcta de NaN → None (no envía NaN a la API)
  - Construcción correcta del record (tipos y campos)
  - Comportamiento ante error de la API
  - Idempotencia conceptual (UPSERT, no INSERT)
"""
import sys
import os
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

ETL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "etl")
sys.path.insert(0, ETL_DIR)

from loaders.supabase_loader import load_to_dim_clima, load_to_staging


class TestLoadToDimClimaVacio:
    """DataFrame vacío siempre retorna 0 sin llamar a la API."""

    def test_df_vacio_retorna_cero(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "fake-key")
        resultado = load_to_dim_clima(pd.DataFrame())
        assert resultado == 0

    def test_df_vacio_sin_credenciales_retorna_cero(self, monkeypatch):
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)
        resultado = load_to_dim_clima(pd.DataFrame())
        assert resultado == 0


class TestLoadToDimClimaDryRun:
    """Sin credenciales, opera en dry-run y retorna len(df)."""

    def test_dry_run_sin_url(self, df_transformado, monkeypatch):
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)
        resultado = load_to_dim_clima(df_transformado)
        assert resultado == len(df_transformado)

    def test_dry_run_sin_key(self, df_transformado, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
        monkeypatch.delenv("SUPABASE_KEY", raising=False)
        resultado = load_to_dim_clima(df_transformado)
        assert resultado == len(df_transformado)


class TestLoadToDimClimaRecords:
    """Verifica la construcción correcta de los records enviados a la API."""

    def _capturar_records(self, df, monkeypatch):
        """Helper: llama al loader mockeando Supabase y captura los records."""
        monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "fake-key")

        captured = {}

        mock_resp = MagicMock()
        mock_resp.data = [{"id": 1}]

        mock_table = MagicMock()
        mock_table.upsert.return_value.execute.return_value = mock_resp

        mock_client = MagicMock()
        mock_client.table.return_value = mock_table

        with patch("loaders.supabase_loader.create_client", return_value=mock_client):
            load_to_dim_clima(df)
            if mock_table.upsert.called:
                captured["records"] = mock_table.upsert.call_args[0][0]
                captured["on_conflict"] = mock_table.upsert.call_args[1].get("on_conflict", "")

        return captured

    def test_campos_obligatorios_en_records(self, df_transformado, monkeypatch):
        info = self._capturar_records(df_transformado, monkeypatch)
        assert "records" in info
        campos_esperados = {
            "localidad_id", "fecha",
            "temp_promedio", "temp_max", "temp_min", "humedad_promedio",
        }
        for record in info["records"]:
            assert campos_esperados.issubset(record.keys()), (
                f"Record sin campos esperados: {record}"
            )

    def test_localidad_id_es_int(self, df_transformado, monkeypatch):
        info = self._capturar_records(df_transformado, monkeypatch)
        for record in info["records"]:
            assert isinstance(record["localidad_id"], int)

    def test_fecha_es_string(self, df_transformado, monkeypatch):
        info = self._capturar_records(df_transformado, monkeypatch)
        for record in info["records"]:
            assert isinstance(record["fecha"], str)

    def test_nan_convertido_a_none(self, monkeypatch):
        """NaN en el DataFrame debe convertirse en None en el record (JSON null)."""
        monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "fake-key")

        # DataFrame con NaN explícito en temp_promedio
        df = pd.DataFrame([{
            "localidad_id":     10,
            "fecha":            "2024-11-03",
            "temp_promedio":    float("nan"),
            "temp_max":         26.0,
            "temp_min":         18.0,
            "humedad_promedio": 62.0,
        }])

        mock_resp = MagicMock()
        mock_resp.data = [{"id": 1}]

        mock_table = MagicMock()
        mock_table.upsert.return_value.execute.return_value = mock_resp

        mock_client = MagicMock()
        mock_client.table.return_value = mock_table

        with patch("loaders.supabase_loader.create_client", return_value=mock_client):
            load_to_dim_clima(df)

        records = mock_table.upsert.call_args[0][0]
        assert records[0]["temp_promedio"] is None, (
            "NaN debe convertirse a None, no enviarse como NaN a la API"
        )

    def test_upsert_usa_conflict_localidad_fecha(self, df_transformado, monkeypatch):
        """El UPSERT debe usar la clave (localidad_id, fecha) para idempotencia."""
        info = self._capturar_records(df_transformado, monkeypatch)
        assert "localidad_id,fecha" in info.get("on_conflict", "")


class TestLoadToDimClimaErrorAPI:
    """Ante errores de la API, retorna 0 sin propagar la excepción."""

    def test_retorna_cero_en_error(self, df_transformado, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "fake-key")

        mock_client = MagicMock()
        mock_client.table.side_effect = Exception("API error 500")

        with patch("loaders.supabase_loader.create_client", return_value=mock_client):
            resultado = load_to_dim_clima(df_transformado)

        assert resultado == 0


class TestCompatibilidadAlias:
    """load_to_staging es un alias de load_to_dim_clima (retrocompat)."""

    def test_alias_apunta_a_misma_funcion(self):
        assert load_to_staging is load_to_dim_clima
