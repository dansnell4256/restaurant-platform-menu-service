"""Component tests for PUT menu item API endpoint.

This test verifies the FastAPI endpoint for updating menu items:
- PUT /menus/{restaurant_id}/items/{item_id} - Update an existing menu item
- Requires X-API-Key header for authentication
- Returns 200 with updated item on success
- Returns 401 if API key is missing or invalid
- Returns 404 if item doesn't exist
- Returns 400 if restaurant_id in body doesn't match path
- Returns 422 if request body fails validation
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
def test_put_item_without_api_key_returns_401(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test PUT /menus/{restaurant_id}/items/{item_id} returns 401 without API key."""
    # Arrange
    item_data = {
        "restaurant_id": "rest_123",
        "item_id": "item_1",
        "name": "Updated Pizza",
        "description": "Updated description",
        "price": "14.99",
        "category": "pizza",
        "availability": True,
        "allergens": ["dairy", "gluten"],
    }

    # Act - No X-API-Key header
    response = client.put("/menus/rest_123/items/item_1", json=item_data)

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key"}
    # Repository should not be called
    mock_repository.update.assert_not_called()


@pytest.mark.component
def test_put_item_with_invalid_api_key_returns_401(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test PUT /menus/{restaurant_id}/items/{item_id} returns 401 with invalid API key."""
    # Arrange
    item_data = {
        "restaurant_id": "rest_123",
        "item_id": "item_1",
        "name": "Updated Pizza",
        "description": "Updated description",
        "price": "14.99",
        "category": "pizza",
        "availability": True,
        "allergens": ["dairy", "gluten"],
    }

    # Act - Invalid API key
    response = client.put(
        "/menus/rest_123/items/item_1",
        json=item_data,
        headers={"X-API-Key": "invalid-key"},
    )

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key"}
    # Repository should not be called
    mock_repository.update.assert_not_called()


@pytest.mark.component
def test_put_item_updates_existing_item(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test PUT /menus/{restaurant_id}/items/{item_id} updates existing item."""
    # Arrange
    item_data = {
        "restaurant_id": "rest_123",
        "item_id": "item_1",
        "name": "Updated Margherita Pizza",
        "description": "Updated classic pizza",
        "price": "14.99",
        "category": "pizza",
        "availability": False,
        "allergens": ["dairy", "gluten", "soy"],
    }

    updated_item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_1",
        name="Updated Margherita Pizza",
        description="Updated classic pizza",
        price=Decimal("14.99"),
        category="pizza",
        availability=False,
        allergens=["dairy", "gluten", "soy"],
    )
    mock_repository.update.return_value = updated_item

    # Act - Valid API key
    response = client.put(
        "/menus/rest_123/items/item_1",
        json=item_data,
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["restaurant_id"] == "rest_123"
    assert json_response["item_id"] == "item_1"
    assert json_response["name"] == "Updated Margherita Pizza"
    assert json_response["description"] == "Updated classic pizza"
    assert json_response["price"] == "14.99"
    assert json_response["availability"] is False
    assert json_response["allergens"] == ["dairy", "gluten", "soy"]

    # Verify repository was called correctly
    mock_repository.update.assert_called_once()
    call_args = mock_repository.update.call_args[0][0]
    assert isinstance(call_args, MenuItem)
    assert call_args.restaurant_id == "rest_123"
    assert call_args.item_id == "item_1"
    assert call_args.name == "Updated Margherita Pizza"


@pytest.mark.component
def test_put_item_returns_404_when_not_found(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test PUT /menus/{restaurant_id}/items/{item_id} returns 404 when item doesn't exist."""
    # Arrange
    item_data = {
        "restaurant_id": "rest_123",
        "item_id": "nonexistent",
        "name": "Updated Pizza",
        "description": "Updated description",
        "price": "14.99",
        "category": "pizza",
        "availability": True,
        "allergens": [],
    }
    mock_repository.update.return_value = None

    # Act - Valid API key
    response = client.put(
        "/menus/rest_123/items/nonexistent",
        json=item_data,
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

    # Verify repository was called
    mock_repository.update.assert_called_once()


@pytest.mark.component
def test_put_item_validates_restaurant_id_matches_path(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test PUT endpoint validates restaurant_id in body matches path parameter."""
    # Arrange - restaurant_id in body doesn't match path
    item_data = {
        "restaurant_id": "rest_456",  # Different from path
        "item_id": "item_1",
        "name": "Updated Pizza",
        "description": "Updated description",
        "price": "14.99",
        "category": "pizza",
        "availability": True,
        "allergens": [],
    }

    # Act - Valid API key
    response = client.put(
        "/menus/rest_123/items/item_1",
        json=item_data,
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 400
    assert "restaurant_id" in response.json()["detail"].lower()
    # Repository should not be called
    mock_repository.update.assert_not_called()


@pytest.mark.component
def test_put_item_validates_item_id_matches_path(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test PUT endpoint validates item_id in body matches path parameter."""
    # Arrange - item_id in body doesn't match path
    item_data = {
        "restaurant_id": "rest_123",
        "item_id": "item_999",  # Different from path
        "name": "Updated Pizza",
        "description": "Updated description",
        "price": "14.99",
        "category": "pizza",
        "availability": True,
        "allergens": [],
    }

    # Act - Valid API key
    response = client.put(
        "/menus/rest_123/items/item_1",
        json=item_data,
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 400
    assert "item_id" in response.json()["detail"].lower()
    # Repository should not be called
    mock_repository.update.assert_not_called()


@pytest.mark.component
def test_put_item_with_incomplete_payload_returns_422(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test PUT endpoint rejects incomplete payload missing required fields."""
    # Arrange - Missing required 'name' field
    item_data = {
        "restaurant_id": "rest_123",
        "item_id": "item_1",
        "description": "Updated description",
        "price": "14.99",
        "category": "pizza",
        "availability": True,
        "allergens": [],
    }

    # Act - Valid API key but incomplete data
    response = client.put(
        "/menus/rest_123/items/item_1",
        json=item_data,
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 422  # Unprocessable Entity (validation error)
    # Repository should not be called
    mock_repository.update.assert_not_called()


@pytest.mark.component
def test_put_item_with_different_restaurant_and_item_ids(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test PUT endpoint works with different restaurant and item IDs."""
    # Arrange
    item_data = {
        "restaurant_id": "rest_456",
        "item_id": "item_999",
        "name": "Updated Caesar Salad",
        "description": "Fresh romaine with updates",
        "price": "9.99",
        "category": "salad",
        "availability": True,
        "allergens": ["dairy"],
    }

    updated_item = MenuItem(
        restaurant_id="rest_456",
        item_id="item_999",
        name="Updated Caesar Salad",
        description="Fresh romaine with updates",
        price=Decimal("9.99"),
        category="salad",
        availability=True,
        allergens=["dairy"],
    )
    mock_repository.update.return_value = updated_item

    # Act - Valid API key
    response = client.put(
        "/menus/rest_456/items/item_999",
        json=item_data,
        headers={"X-API-Key": "test-key-456"},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["restaurant_id"] == "rest_456"
    assert response.json()["item_id"] == "item_999"
    assert response.json()["name"] == "Updated Caesar Salad"
    mock_repository.update.assert_called_once()
