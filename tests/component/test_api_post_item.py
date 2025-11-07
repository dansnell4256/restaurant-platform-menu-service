"""Component tests for POST menu item API endpoint.

This test verifies the FastAPI endpoint for creating menu items:
- POST /restaurants/{restaurant_id}/items - Create a new menu item
- Requires X-API-Key header for authentication
- Returns 201 with created item on success
- Returns 401 if API key is missing or invalid
- Returns 400 if restaurant_id in body doesn't match path
- Returns 422 if request body fails validation
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
def test_post_item_without_api_key_returns_401(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test POST /restaurants/{restaurant_id}/items returns 401 without API key."""
    # Arrange
    item_data = {
        "restaurant_id": "rest_123",
        "item_id": "item_1",
        "name": "Margherita Pizza",
        "description": "Classic pizza with tomato and mozzarella",
        "price": "12.99",
        "category": "pizza",
        "availability": True,
        "allergens": ["dairy", "gluten"],
    }

    # Act - No X-API-Key header
    response = client.post("/restaurants/rest_123/items", json=item_data)

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key"}
    # Repository should not be called
    mock_repository.create.assert_not_called()


@pytest.mark.component
def test_post_item_with_invalid_api_key_returns_401(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test POST /restaurants/{restaurant_id}/items returns 401 with invalid API key."""
    # Arrange
    item_data = {
        "restaurant_id": "rest_123",
        "item_id": "item_1",
        "name": "Margherita Pizza",
        "description": "Classic pizza with tomato and mozzarella",
        "price": "12.99",
        "category": "pizza",
        "availability": True,
        "allergens": ["dairy", "gluten"],
    }

    # Act - Invalid API key
    response = client.post(
        "/restaurants/rest_123/items",
        json=item_data,
        headers={"X-API-Key": "invalid-key"},
    )

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key"}
    # Repository should not be called
    mock_repository.create.assert_not_called()


@pytest.mark.component
def test_post_item_creates_new_item(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test POST /restaurants/{restaurant_id}/items creates new menu item."""
    # Arrange
    item_data = {
        "restaurant_id": "rest_123",
        "item_id": "item_1",
        "name": "Margherita Pizza",
        "description": "Classic pizza with tomato and mozzarella",
        "price": "12.99",
        "category": "pizza",
        "availability": True,
        "allergens": ["dairy", "gluten"],
    }

    created_item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_1",
        name="Margherita Pizza",
        description="Classic pizza with tomato and mozzarella",
        price=Decimal("12.99"),
        category="pizza",
        availability=True,
        allergens=["dairy", "gluten"],
    )
    mock_repository.create.return_value = created_item

    # Act - Valid API key
    response = client.post(
        "/restaurants/rest_123/items",
        json=item_data,
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 201
    json_response = response.json()
    assert json_response["restaurant_id"] == "rest_123"
    assert json_response["item_id"] == "item_1"
    assert json_response["name"] == "Margherita Pizza"
    assert json_response["description"] == "Classic pizza with tomato and mozzarella"
    assert json_response["price"] == "12.99"
    assert json_response["category"] == "pizza"
    assert json_response["availability"] is True
    assert json_response["allergens"] == ["dairy", "gluten"]

    # Verify repository was called with correct data
    mock_repository.create.assert_called_once()
    call_args = mock_repository.create.call_args[0][0]
    assert isinstance(call_args, MenuItem)
    assert call_args.restaurant_id == "rest_123"
    assert call_args.item_id == "item_1"
    assert call_args.name == "Margherita Pizza"


@pytest.mark.component
def test_post_item_validates_restaurant_id_matches_path(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test POST endpoint validates restaurant_id in body matches path parameter."""
    # Arrange - restaurant_id in body doesn't match path
    item_data = {
        "restaurant_id": "rest_456",  # Different from path
        "item_id": "item_1",
        "name": "Margherita Pizza",
        "description": "Classic pizza",
        "price": "12.99",
        "category": "pizza",
        "availability": True,
        "allergens": [],
    }

    # Act - Valid API key
    response = client.post(
        "/restaurants/rest_123/items",
        json=item_data,
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 400
    assert "restaurant_id" in response.json()["detail"].lower()
    # Repository should not be called
    mock_repository.create.assert_not_called()


@pytest.mark.component
def test_post_item_with_incomplete_payload_returns_422(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test POST endpoint rejects incomplete payload missing required fields."""
    # Arrange - Missing required 'name' field
    item_data = {
        "restaurant_id": "rest_123",
        "item_id": "item_1",
        "description": "Classic pizza",
        "price": "12.99",
        "category": "pizza",
        "availability": True,
        "allergens": [],
    }

    # Act - Valid API key but incomplete data
    response = client.post(
        "/restaurants/rest_123/items",
        json=item_data,
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 422  # Unprocessable Entity (validation error)
    # Repository should not be called
    mock_repository.create.assert_not_called()
