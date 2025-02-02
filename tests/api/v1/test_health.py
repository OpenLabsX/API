from fastapi import status
from fastapi.testclient import TestClient

from src.app.main import app

from .config import BASE_ROUTE

client = TestClient(app)


def test_ping_check() -> None:
    """Test that the /health/ping endpoint returns pong response."""
    response = client.get(f"{BASE_ROUTE}/health/ping")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"msg": "pong"}
