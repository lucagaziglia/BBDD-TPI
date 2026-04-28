"""
test_mongodb_extractor.py — Tests del extractor de MongoDB.

Cubre:
  - Fallback a datos mock cuando MONGODB_URI no está configurado
  - Estructura de documentos retornados
  - Comportamiento con variables de entorno configuradas (conexión rechazada)
"""
import os
import sys
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Path fix — añade etl/ al path para importar extractors directamente
ETL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "etl")
sys.path.insert(0, ETL_DIR)

from extractors.mongodb_extractor import extract_sensor_readings, MOCK_READINGS


class TestExtractSensorReadingsMock:
    """Cuando MONGODB_URI no está configurado, usa datos mock."""

    def test_retorna_mock_sin_uri(self, monkeypatch):
        """Sin MONGODB_URI definida, retorna MOCK_READINGS."""
        monkeypatch.delenv("MONGODB_URI", raising=False)
        resultado = extract_sensor_readings(
            desde=datetime(2024, 1, 1),
            hasta=datetime(2024, 12, 31),
        )
        assert resultado == MOCK_READINGS

    def test_mock_no_vacio(self):
        """MOCK_READINGS tiene al menos un documento."""
        assert len(MOCK_READINGS) > 0

    def test_mock_estructura_documentos(self):
        """Cada doc mock tiene los campos obligatorios con tipos correctos."""
        campos_requeridos = {"lote_id", "timestamp", "tipo_lectura", "valor"}
        for doc in MOCK_READINGS:
            assert campos_requeridos.issubset(doc.keys()), (
                f"Documento sin campos esperados: {doc}"
            )
            assert isinstance(doc["lote_id"], int)
            assert isinstance(doc["timestamp"], datetime)
            assert doc["tipo_lectura"] in ("HUMEDAD_SUELO", "TEMPERATURA")
            assert isinstance(doc["valor"], (int, float))

    def test_mock_valores_en_rango(self):
        """Los valores mock están dentro de los rangos físicamente razonables."""
        for doc in MOCK_READINGS:
            if doc["tipo_lectura"] == "HUMEDAD_SUELO":
                assert 0 <= doc["valor"] <= 100, f"Humedad fuera de rango: {doc['valor']}"
            elif doc["tipo_lectura"] == "TEMPERATURA":
                assert -30 <= doc["valor"] <= 60, f"Temperatura fuera de rango: {doc['valor']}"

    def test_mock_lote_ids_validos(self):
        """Todos los lote_id en el mock son enteros positivos."""
        for doc in MOCK_READINGS:
            assert doc["lote_id"] > 0


class TestExtractSensorReadingsConexionFallida:
    """Cuando la URI está definida pero la conexión falla, retorna lista vacía."""

    def test_retorna_lista_vacia_en_error(self, monkeypatch):
        """Si MongoDB no es alcanzable, retorna [] sin propagar excepción."""
        monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27099/fake")

        with patch("extractors.mongodb_extractor.MongoClient") as mock_client:
            # Simular timeout de conexión
            mock_client.side_effect = Exception("ServerSelectionTimeoutError")

            resultado = extract_sensor_readings(
                desde=datetime(2024, 1, 1),
                hasta=datetime(2024, 12, 31),
            )
        assert resultado == []

    def test_retorna_lista_en_error_de_query(self, monkeypatch):
        """Si la query a la colección falla, retorna [] sin romper el pipeline."""
        monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27099/fake")

        mock_col = MagicMock()
        mock_col.find.side_effect = Exception("Cursor error")

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_col

        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__.return_value = mock_db

        with patch("extractors.mongodb_extractor.MongoClient", return_value=mock_client_instance):
            resultado = extract_sensor_readings(
                desde=datetime(2024, 1, 1),
                hasta=datetime(2024, 12, 31),
            )
        assert resultado == []


class TestExtractSensorReadingsConexionExitosa:
    """Simula una conexión exitosa a MongoDB devolviendo documentos de prueba."""

    def test_retorna_documentos_de_mongodb(self, monkeypatch, raw_readings_validos):
        """Cuando la conexión es exitosa, retorna los documentos de la colección."""
        monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017/fake")

        mock_col = MagicMock()
        mock_col.find.return_value = raw_readings_validos

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_col

        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__.return_value = mock_db

        with patch("extractors.mongodb_extractor.MongoClient", return_value=mock_client_instance):
            resultado = extract_sensor_readings(
                desde=datetime(2024, 11, 1),
                hasta=datetime(2024, 11, 30),
            )

        assert len(resultado) == len(raw_readings_validos)

    def test_query_usa_rango_de_fechas(self, monkeypatch):
        """La query enviada a MongoDB incluye el filtro de timestamp correcto."""
        monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017/fake")

        desde = datetime(2024, 11, 1)
        hasta  = datetime(2024, 11, 30)

        mock_col = MagicMock()
        mock_col.find.return_value = []

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_col

        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__.return_value = mock_db

        with patch("extractors.mongodb_extractor.MongoClient", return_value=mock_client_instance):
            extract_sensor_readings(desde=desde, hasta=hasta)

        called_query = mock_col.find.call_args[0][0]
        assert "$gte" in called_query["timestamp"]
        assert "$lte" in called_query["timestamp"]
        assert called_query["timestamp"]["$gte"] == desde
        assert called_query["timestamp"]["$lte"] == hasta
