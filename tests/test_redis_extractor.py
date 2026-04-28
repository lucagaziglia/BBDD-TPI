"""
test_redis_extractor.py — Tests del extractor de Redis.

Cubre:
  - Fallback a datos mock cuando REDIS_URL no está configurado
  - Estructura de keys y valores del mock
  - Comportamiento ante conexión rechazada
  - Parseo de keys (sensor:*, riego:*)
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

ETL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "etl")
sys.path.insert(0, ETL_DIR)

from extractors.redis_extractor import extract_realtime_state, MOCK_STATE


class TestExtractRealtimeStateMock:
    """Cuando REDIS_URL no está configurada, retorna MOCK_STATE."""

    def test_retorna_mock_sin_url(self, monkeypatch):
        """Sin REDIS_URL, retorna el estado mock completo."""
        monkeypatch.delenv("REDIS_URL", raising=False)
        resultado = extract_realtime_state()
        assert resultado == MOCK_STATE

    def test_mock_no_vacio(self):
        """MOCK_STATE tiene al menos una key."""
        assert len(MOCK_STATE) > 0

    def test_mock_contiene_sensores(self):
        """MOCK_STATE incluye keys de sensores (sensor:*:humedad y sensor:*:temperatura)."""
        humedades    = [k for k in MOCK_STATE if ":humedad" in k]
        temperaturas = [k for k in MOCK_STATE if ":temperatura" in k]
        assert len(humedades)    > 0, "Faltan keys de humedad en MOCK_STATE"
        assert len(temperaturas) > 0, "Faltan keys de temperatura en MOCK_STATE"

    def test_mock_contiene_riego(self):
        """MOCK_STATE incluye keys de estado de riego (riego:*:estado)."""
        riegos = [k for k in MOCK_STATE if k.startswith("riego:")]
        assert len(riegos) > 0, "Faltan keys de riego en MOCK_STATE"

    def test_mock_estado_riego_validos(self):
        """Los estados de riego son solo 'ON' o 'OFF'."""
        for key, val in MOCK_STATE.items():
            if key.startswith("riego:"):
                assert val in ("ON", "OFF"), f"Estado inválido para {key}: {val}"

    def test_mock_valores_numericos_parseables(self):
        """Los valores de sensor son strings que se pueden convertir a float."""
        for key, val in MOCK_STATE.items():
            if "sensor:" in key:
                try:
                    float(val)
                except (ValueError, TypeError):
                    pytest.fail(f"Valor no parseable como float en {key}: {val!r}")

    def test_mock_estructura_keys(self):
        """Todas las keys siguen el patrón sensor:{id}:{tipo} o riego:{id}:estado."""
        for key in MOCK_STATE:
            partes = key.split(":")
            assert len(partes) == 3, f"Key con formato inesperado: {key}"
            assert partes[0] in ("sensor", "riego"), f"Prefijo desconocido en: {key}"
            assert partes[1].isdigit(), f"lote_id no es numérico en: {key}"


class TestExtractRealtimeStateConexionFallida:
    """Cuando la URL está configurada pero la conexión falla, retorna {}."""

    def test_retorna_vacio_en_error_de_conexion(self, monkeypatch):
        """Si Redis no es alcanzable, retorna dict vacío sin propagar excepción."""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6399")

        with patch("extractors.redis_extractor.redis.Redis") as mock_redis_cls:
            mock_redis_cls.from_url.side_effect = Exception("Connection refused")
            resultado = extract_realtime_state()

        assert resultado == {}

    def test_retorna_vacio_en_error_de_scan(self, monkeypatch):
        """Si el scan_iter falla, retorna dict vacío."""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6399")

        mock_r = MagicMock()
        mock_r.scan_iter.side_effect = Exception("SCAN error")

        with patch("extractors.redis_extractor.redis.Redis") as mock_redis_cls:
            mock_redis_cls.from_url.return_value = mock_r
            resultado = extract_realtime_state()

        assert resultado == {}


class TestExtractRealtimeStateConexionExitosa:
    """Simula una conexión exitosa y verifica el comportamiento del scan."""

    def test_retorna_keys_de_scan_iter(self, monkeypatch):
        """Con Redis disponible, retorna todas las keys encontradas por scan_iter."""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")

        mock_r = MagicMock()
        # scan_iter("sensor:*") devuelve estas keys
        def scan_iter_side_effect(pattern):
            if pattern == "sensor:*":
                return ["sensor:1:humedad", "sensor:1:temperatura"]
            if pattern == "riego:*":
                return ["riego:1:estado"]
            return []

        mock_r.scan_iter.side_effect = scan_iter_side_effect
        mock_r.get.side_effect = lambda k: {
            "sensor:1:humedad":     "62.3",
            "sensor:1:temperatura": "21.4",
            "riego:1:estado":       "ON",
        }.get(k)

        with patch("extractors.redis_extractor.redis.Redis") as mock_cls:
            mock_cls.from_url.return_value = mock_r
            resultado = extract_realtime_state()

        assert "sensor:1:humedad"     in resultado
        assert "sensor:1:temperatura" in resultado
        assert "riego:1:estado"       in resultado
        assert resultado["riego:1:estado"] == "ON"

    def test_usa_scan_iter_no_keys(self, monkeypatch):
        """Verifica que se usa scan_iter (no r.keys()) para evitar bloqueos."""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")

        mock_r = MagicMock()
        mock_r.scan_iter.return_value = []

        with patch("extractors.redis_extractor.redis.Redis") as mock_cls:
            mock_cls.from_url.return_value = mock_r
            extract_realtime_state()

        # r.keys() jamás debe ser llamado
        mock_r.keys.assert_not_called()
        # scan_iter sí debe ser llamado (al menos una vez)
        assert mock_r.scan_iter.call_count >= 1
