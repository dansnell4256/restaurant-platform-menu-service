"""Component tests for GET single menu item API endpoint.

This test verifies the FastAPI endpoint for retrieving a single menu item:
- GET /menus/{restaurant_id}/items/{item_id} - Get a specific menu item
- Requires X-API-Key header for authentication
- Returns 200 with the item if found
- Returns 404 if item doesn't exist
- Returns 401 if API key is missing or invalid
"""

from collections.abc import Generator
from decimal import Decimal
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.api.menu_items import create_app
from src.models.menu_item_model import MenuItem
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
def test_get_item_without_api_key_returns_401(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET /menus/{restaurant_id}/items/{item_id} returns 401 without API key."""
    # Act - No X-API-Key header
    response = client.get("/menus/rest_123/items/item_1")

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key"}
    # Repository should not be called
    mock_repository.get.assert_not_called()


@pytest.mark.component
def test_get_item_with_invalid_api_key_returns_401(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET /menus/{restaurant_id}/items/{item_id} returns 401 with invalid API key."""
    # Act - Invalid API key
    response = client.get(
        "/menus/rest_123/items/item_1",
        headers={"X-API-Key": "invalid-key"},
    )

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key"}
    # Repository should not be called
    mock_repository.get.assert_not_called()


@pytest.mark.component
def test_get_item_returns_item_when_found(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET /menus/{restaurant_id}/items/{item_id} returns item when found."""
    # Arrange
    item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_1",
        name="Margherita Pizza",
        description="Classic pizza with tomato and mozzarella",
        price=Decimal("12.99"),
        category="pizza",
        availability=True,
        allergens=["dairy", "gluten"],
    )
    mock_repository.get.return_value = item

    # Act - Valid API key
    response = client.get(
        "/menus/rest_123/items/item_1",
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["restaurant_id"] == "rest_123"
    assert json_response["item_id"] == "item_1"
    assert json_response["name"] == "Margherita Pizza"
    assert json_response["description"] == "Classic pizza with tomato and mozzarella"
    assert json_response["price"] == "12.99"
    assert json_response["category"] == "pizza"
    assert json_response["availability"] is True
    assert json_response["allergens"] == ["dairy", "gluten"]

    # Verify repository was called correctly
    mock_repository.get.assert_called_once_with("rest_123", "item_1")


@pytest.mark.component
def test_get_item_returns_404_when_not_found(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET /menus/{restaurant_id}/items/{item_id} returns 404 when item doesn't exist."""
    # Arrange
    mock_repository.get.return_value = None

    # Act - Valid API key
    response = client.get(
        "/menus/rest_123/items/nonexistent",
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

    # Verify repository was called
    mock_repository.get.assert_called_once_with("rest_123", "nonexistent")


@pytest.mark.component
def test_get_item_with_different_restaurant_and_item_ids(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET endpoint works with different restaurant and item IDs."""
    # Arrange
    item = MenuItem(
        restaurant_id="rest_456",
        item_id="item_999",
        name="Caesar Salad",
        description="Fresh romaine",
        price=Decimal("8.99"),
        category="salad",
        availability=True,
        allergens=[],
    )
    mock_repository.get.return_value = item

    # Act - Valid API key
    response = client.get(
        "/menus/rest_456/items/item_999",
        headers={"X-API-Key": "test-key-456"},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["restaurant_id"] == "rest_456"
    assert response.json()["item_id"] == "item_999"
    mock_repository.get.assert_called_once_with("rest_456", "item_999")
