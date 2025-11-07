"""Component tests for menu items API endpoints.

This test verifies the FastAPI endpoints for menu item operations:
- GET /menus/{restaurant_id}/items - List all items for a restaurant
- Requires X-API-Key header for authentication
- Returns 200 with list of items (empty list if none exist)
- Returns 401 if API key is missing or invalid
- Properly formats MenuItem objects as JSON responses
"""

from collections.abc import Generator
from decimal import Decimal
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.api.menu_items import create_app
from src.models.menu_item import MenuItem
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
def test_get_items_without_api_key_returns_401(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET /menus/{restaurant_id}/items returns 401 without API key."""
    # Act - No X-API-Key header
    response = client.get("/menus/rest_123/items")

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key"}
    # Repository should not be called
    mock_repository.list_by_restaurant.assert_not_called()


@pytest.mark.component
def test_get_items_with_invalid_api_key_returns_401(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET /menus/{restaurant_id}/items returns 401 with invalid API key."""
    # Act - Invalid API key
    response = client.get(
        "/menus/rest_123/items",
        headers={"X-API-Key": "invalid-key"},
    )

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key"}
    # Repository should not be called
    mock_repository.list_by_restaurant.assert_not_called()


@pytest.mark.component
def test_get_items_returns_empty_list_when_no_items(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET /menus/{restaurant_id}/items returns empty list when no items exist."""
    # Arrange
    mock_repository.list_by_restaurant.return_value = []

    # Act - Valid API key
    response = client.get(
        "/menus/rest_123/items",
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == []
    mock_repository.list_by_restaurant.assert_called_once_with("rest_123")


@pytest.mark.component
def test_get_items_returns_list_of_items(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET /menus/{restaurant_id}/items returns list of items."""
    # Arrange
    items = [
        MenuItem(
            restaurant_id="rest_123",
            item_id="item_1",
            name="Margherita Pizza",
            description="Classic pizza with tomato and mozzarella",
            price=Decimal("12.99"),
            category="pizza",
            availability=True,
            allergens=["dairy", "gluten"],
        ),
        MenuItem(
            restaurant_id="rest_123",
            item_id="item_2",
            name="Caesar Salad",
            description="Fresh romaine with Caesar dressing",
            price=Decimal("8.99"),
            category="salad",
            availability=True,
            allergens=["dairy", "eggs"],
        ),
    ]
    mock_repository.list_by_restaurant.return_value = items

    # Act - Valid API key
    response = client.get(
        "/menus/rest_123/items",
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 2

    # Verify first item
    assert json_response[0]["restaurant_id"] == "rest_123"
    assert json_response[0]["item_id"] == "item_1"
    assert json_response[0]["name"] == "Margherita Pizza"
    assert json_response[0]["description"] == "Classic pizza with tomato and mozzarella"
    assert json_response[0]["price"] == "12.99"
    assert json_response[0]["category"] == "pizza"
    assert json_response[0]["availability"] is True
    assert json_response[0]["allergens"] == ["dairy", "gluten"]

    # Verify second item
    assert json_response[1]["restaurant_id"] == "rest_123"
    assert json_response[1]["item_id"] == "item_2"
    assert json_response[1]["name"] == "Caesar Salad"

    mock_repository.list_by_restaurant.assert_called_once_with("rest_123")


@pytest.mark.component
def test_get_items_with_different_restaurant_id(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET endpoint works with different restaurant IDs."""
    # Arrange
    mock_repository.list_by_restaurant.return_value = []

    # Act - Valid API key
    response = client.get(
        "/menus/rest_456/items",
        headers={"X-API-Key": "test-key-456"},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == []
    mock_repository.list_by_restaurant.assert_called_once_with("rest_456")


@pytest.mark.component
def test_get_items_with_alternate_valid_api_key(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET endpoint accepts alternate valid API key."""
    # Arrange
    mock_repository.list_by_restaurant.return_value = []

    # Act - Different valid API key
    response = client.get(
        "/menus/rest_123/items",
        headers={"X-API-Key": "test-key-456"},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == []
    mock_repository.list_by_restaurant.assert_called_once_with("rest_123")
