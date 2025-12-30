# === Файл: tests/test_api/test_endpoints.py (обновлённый) ===
"""Тесты для API endpoints."""

import pytest
from fastapi.testclient import TestClient

from avatar.api.app import create_app
from avatar.config.settings import Settings


@pytest.fixture
def test_app():
    """Фикстура для тестового FastAPI приложения."""
    settings = Settings()
    return create_app(settings)


@pytest.fixture
def client(test_app):
    """Фикстура для TestClient."""
    return TestClient(test_app)


def test_health_endpoint(client):
    """Тест GET /api/v1/health."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["healthy", "unhealthy"]
    assert "components" in data
    assert "llm" in data["components"]
    assert "tts" in data["components"]


def test_chat_endpoint_success(client):
    """Тест POST /api/v1/chat с корректным запросом."""
    payload = {
        "message": "Привет!",
        "conversation_history": None,
    }

    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "full_text" in data
    assert "audio" in data
    assert "audio_bytes_base64" in data["audio"]
    assert "blendshapes" in data
    assert "motion" in data
    assert "processing_time" in data


def test_chat_endpoint_empty_message(client):
    """Тест POST /api/v1/chat с пустым сообщением."""
    payload = {"message": ""}

    response = client.post("/api/v1/chat", json=payload)
    # Pydantic field validator возвращает 422
    assert response.status_code == 422


def test_chat_endpoint_too_long(client):
    """Тест POST /api/v1/chat со слишком длинным сообщением."""
    payload = {"message": "a" * 2001}

    response = client.post("/api/v1/chat", json=payload)
    # Pydantic field validator возвращает 422
    assert response.status_code == 422
