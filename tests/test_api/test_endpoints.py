"""Тесты для API endpoints."""

import pytest
from fastapi.testclient import TestClient
from avatar.api.app import create_app
from avatar.config import Settings


@pytest.fixture
def client():
    """Фикстура для тестового HTTP-клиента."""
    app = create_app(Settings())
    return TestClient(app)


def test_health_endpoint(client):
    """Тест GET /api/v1/health."""
    response = client.get("/api/v1/health")
    
    # Раскомментируйте после реализации healthcheck:
    # assert response.status_code == 200
    # data = response.json()
    # assert "status" in data
    # assert "components" in data


def test_chat_endpoint(client):
    """Тест POST /api/v1/chat."""
    response = client.post(
        "/api/v1/chat",
        json={"message": "Привет!"},
    )
    
    # Раскомментируйте после реализации chat:
    # assert response.status_code == 200
    # data = response.json()
    # assert "full_text" in data
