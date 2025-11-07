"""Component tests for DELETE menu item API endpoint.

This test verifies the FastAPI endpoint for deleting menu items:
- DELETE /menus/{restaurant_id}/items/{item_id} - Delete a menu item
- Requires X-API-Key header for authentication
- Returns 204 No Content on successful deletion
- Returns 401 if API key is missing or invalid
- Returns 404 if item doesn't exist
"""

from collections.abc import Generator
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.api.menu_items import create_app
from src.security.api_key_validator import APIKeyValidator


@pytest.fixture
def mock_repository() -> Mock:
    """Create a mock MenuItemRepository for testing."""
    return Mock()


@pytest.fixture
def api_key_validator() -> APIKeyValidator:
    """Create API key validator with test keys."""
    return APIKeyValidator(valid_keys={"test-key-123", "test-key-456"})


@pytest.fixture
def client(
    mock_repository: Mock,
    api_key_validator: APIKeyValidator,
) -> Generator[TestClient, None, None]:
    """Create FastAPI test client with mocked repository and validator."""
    app = create_app(repository=mock_repository, api_key_validator=api_key_validator)
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.component
def test_delete_item_without_api_key_returns_401(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test DELETE /menus/{restaurant_id}/items/{item_id} returns 401 without API key."""
    # Act - No X-API-Key header
    response = client.delete("/menus/rest_123/items/item_1")

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key"}
    # Repository should not be called
    mock_repository.delete.assert_not_called()


@pytest.mark.component
def test_delete_item_with_invalid_api_key_returns_401(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test DELETE /menus/{restaurant_id}/items/{item_id} returns 401 with invalid API key."""
    # Act - Invalid API key
    response = client.delete(
        "/menus/rest_123/items/item_1",
        headers={"X-API-Key": "invalid-key"},
    )

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key"}
    # Repository should not be called
    mock_repository.delete.assert_not_called()


@pytest.mark.component
def test_delete_item_deletes_successfully(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test DELETE /menus/{restaurant_id}/items/{item_id} deletes item successfully."""
    # Arrange
    mock_repository.delete.return_value = True

    # Act - Valid API key
    response = client.delete(
        "/menus/rest_123/items/item_1",
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 204
    assert response.content == b""  # No content returned on successful delete

    # Verify repository was called correctly
    mock_repository.delete.assert_called_once_with("rest_123", "item_1")


@pytest.mark.component
def test_delete_item_returns_404_when_not_found(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test DELETE /menus/{restaurant_id}/items/{item_id} returns 404 when item doesn't exist."""
    # Arrange
    mock_repository.delete.return_value = False

    # Act - Valid API key
    response = client.delete(
        "/menus/rest_123/items/nonexistent",
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

    # Verify repository was called
    mock_repository.delete.assert_called_once_with("rest_123", "nonexistent")


@pytest.mark.component
def test_delete_item_with_different_restaurant_and_item_ids(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test DELETE endpoint works with different restaurant and item IDs."""
    # Arrange
    mock_repository.delete.return_value = True

    # Act - Valid API key
    response = client.delete(
        "/menus/rest_456/items/item_999",
        headers={"X-API-Key": "test-key-456"},
    )

    # Assert
    assert response.status_code == 204
    assert response.content == b""  # No content returned
    mock_repository.delete.assert_called_once_with("rest_456", "item_999")
