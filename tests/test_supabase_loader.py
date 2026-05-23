"""
test_supabase_loader.py — Tests del loader de Supabase.

Cubre:
  - DataFrame vacío → retorna 0
  - Faltan credenciales → retorna 0 (no rompe)
  - Construcción correcta del UPSERT (records + on_conflict)
  - Conversión de fecha a string para que sea serializable
  - Comportamiento ante error de la API
"""
import os
import sys
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

ETL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "etl")
sys.path.insert(0, ETL_DIR)

from loaders.supabase_loader import load_to_mediciones_diarias


def _make_df():
    """DataFrame con las columnas que produce el transformer."""
    return pd.DataFrame([{
        "lote_id":            1,
        "fecha":              "2024-11-03",
        "mes":                11,
        "temp_prom":          21.5,
        "temp_max":           22.0,
        "temp_min":           18.0,
        "humedad_prom":       62.0,
        "precipitacion_mm":   0.0,
        "m3_agua_consumida":  30.0,
    }])


class TestLoadVacio:
    """DataFrame vacío siempre retorna 0 sin llamar a la API."""

    def test_df_vacio_retorna_cero(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "fake-key")
        assert load_to_mediciones_diarias(pd.DataFrame()) == 0

    def test_df_vacio_sin_credenciales_retorna_cero(self, monkeypatch):
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
        assert load_to_mediciones_diarias(pd.DataFrame()) == 0


class TestLoadSinCredenciales:
    """Sin credenciales, no debe llamar a la API y retorna 0."""

    def test_sin_url_retorna_cero(self, monkeypatch):
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.setenv("SUPABASE_ANON_KEY", "fake-key")
        assert load_to_mediciones_diarias(_make_df()) == 0

    def test_sin_key_retorna_cero(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
        monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
        assert load_to_mediciones_diarias(_make_df()) == 0


class TestLoadRecords:
    """Verifica la construcción correcta de los records enviados al UPSERT."""

    def _capturar_call(self, df, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "fake-key")

        captured = {}

        mock_resp = MagicMock()
        mock_resp.data = [{"id": 1}]

        mock_table = MagicMock()
        mock_table.upsert.return_value.execute.return_value = mock_resp

        mock_client = MagicMock()
        mock_client.table.return_value = mock_table

        with patch("loaders.supabase_loader.create_client", return_value=mock_client):
            load_to_mediciones_diarias(df)
            if mock_table.upsert.called:
                captured["records"]      = mock_table.upsert.call_args[0][0]
                captured["on_conflict"]  = mock_table.upsert.call_args[1].get("on_conflict", "")
                captured["table_name"]   = mock_client.table.call_args[0][0]

        return captured

    def test_usa_tabla_dim_mediciones_diarias(self, monkeypatch):
        info = self._capturar_call(_make_df(), monkeypatch)
        assert info["table_name"] == "dim_mediciones_diarias"

    def test_campos_obligatorios_en_records(self, monkeypatch):
        info = self._capturar_call(_make_df(), monkeypatch)
        campos_esperados = {
            "lote_id", "fecha", "mes",
            "temp_prom", "temp_max", "temp_min",
            "humedad_prom", "precipitacion_mm", "m3_agua_consumida",
        }
        for record in info["records"]:
            assert campos_esperados.issubset(record.keys())

    def test_fecha_es_string(self, monkeypatch):
        """La fecha debe enviarse como string ISO para que Supabase la acepte."""
        info = self._capturar_call(_make_df(), monkeypatch)
        for record in info["records"]:
            assert isinstance(record["fecha"], str)

    def test_upsert_usa_conflict_lote_id_fecha(self, monkeypatch):
        """El UPSERT usa (lote_id, fecha) como clave de conflicto (idempotencia)."""
        info = self._capturar_call(_make_df(), monkeypatch)
        on_conflict = info["on_conflict"].replace(" ", "")
        assert "lote_id" in on_conflict
        assert "fecha"   in on_conflict


class TestLoadErrorAPI:
    """Ante error de la API, retorna 0 sin propagar la excepción."""

    def test_retorna_cero_en_error(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "fake-key")

        mock_client = MagicMock()
        mock_client.table.side_effect = Exception("API error 500")

        with patch("loaders.supabase_loader.create_client", return_value=mock_client):
            resultado = load_to_mediciones_diarias(_make_df())

        assert resultado == 0
