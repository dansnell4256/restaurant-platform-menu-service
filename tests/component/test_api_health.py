"""Component tests for health check endpoint.

This test verifies the FastAPI health check endpoint:
- GET /health - Returns service health status
- Does NOT require API key authentication (public endpoint)
- Returns 200 with status and service information
- Used by load balancers and monitoring systems
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from src.api.health import create_app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create FastAPI test client for health endpoint."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.component
def test_health_check_returns_200(client: TestClient) -> None:
    """Test GET /health returns 200 OK."""
    # Act
    response = client.get("/health")

    # Assert
    assert response.status_code == 200


@pytest.mark.component
def test_health_check_returns_status_ok(client: TestClient) -> None:
    """Test GET /health returns status field with 'ok' value."""
    # Act
    response = client.get("/health")

    # Assert
    json_response = response.json()
    assert "status" in json_response
    assert json_response["status"] == "ok"


@pytest.mark.component
def test_health_check_returns_service_name(client: TestClient) -> None:
    """Test GET /health returns service identification."""
    # Act
    response = client.get("/health")

    # Assert
    json_response = response.json()
    assert "service" in json_response
    assert json_response["service"] == "menu-service"


@pytest.mark.component
def test_health_check_does_not_require_api_key(client: TestClient) -> None:
    """Test GET /health is accessible without API key (public endpoint)."""
    # Act - No X-API-Key header
    response = client.get("/health")

    # Assert
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.component
def test_health_check_includes_version(client: TestClient) -> None:
    """Test GET /health includes version information."""
    # Act
    response = client.get("/health")

    # Assert
    json_response = response.json()
    assert "version" in json_response
    assert isinstance(json_response["version"], str)
    assert len(json_response["version"]) > 0
