"""Component tests for restaurant authorization in API endpoints.

This test verifies that API keys can only access restaurants they're authorized for:
- API key with specific restaurant permissions can only access those restaurants
- API key without permission for a restaurant gets 403 Forbidden
- Admin key with wildcard (*) can access all restaurants
- Valid API key is required (401) before checking restaurant access (403)
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
    """Create API key validator with restaurant permissions."""
    return APIKeyValidator(
        valid_keys={"key-rest-123", "key-rest-456", "admin-key"},
        key_permissions={
            "key-rest-123": ["rest_123"],  # Can only access rest_123
            "key-rest-456": ["rest_456"],  # Can only access rest_456
            "admin-key": ["*"],  # Can access all restaurants
        },
    )


@pytest.fixture
def client(
    mock_repository: Mock,
    api_key_validator: APIKeyValidator,
) -> Generator[TestClient, None, None]:
    """Create FastAPI test client with mocked repository and validator."""
    app = create_app(repository=mock_repository, api_key_validator=api_key_validator)
    with TestClient(app) as test_client:
        yield test_client


# GET /menus/{restaurant_id}/items - List items authorization tests


@pytest.mark.component
def test_get_items_with_authorized_key_succeeds(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET items succeeds when API key has permission for restaurant."""
    # Arrange
    mock_repository.list_by_restaurant.return_value = []

    # Act - API key authorized for rest_123
    response = client.get(
        "/menus/rest_123/items",
        headers={"X-API-Key": "key-rest-123"},
    )

    # Assert
    assert response.status_code == 200
    mock_repository.list_by_restaurant.assert_called_once_with("rest_123")


@pytest.mark.component
def test_get_items_with_unauthorized_key_returns_403(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET items returns 403 when API key doesn't have permission for restaurant."""
    # Act - API key NOT authorized for rest_456 (only authorized for rest_123)
    response = client.get(
        "/menus/rest_456/items",
        headers={"X-API-Key": "key-rest-123"},
    )

    # Assert
    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()
    # Repository should not be called
    mock_repository.list_by_restaurant.assert_not_called()


@pytest.mark.component
def test_get_items_with_admin_key_succeeds_for_any_restaurant(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET items succeeds with admin key (wildcard) for any restaurant."""
    # Arrange
    mock_repository.list_by_restaurant.return_value = []

    # Act - Admin key with wildcard access
    response = client.get(
        "/menus/rest_999/items",
        headers={"X-API-Key": "admin-key"},
    )

    # Assert
    assert response.status_code == 200
    mock_repository.list_by_restaurant.assert_called_once_with("rest_999")


# POST /menus/{restaurant_id}/items - Create item authorization tests


@pytest.mark.component
def test_post_item_with_authorized_key_succeeds(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test POST item succeeds when API key has permission for restaurant."""
    # Arrange
    item_data = {
        "restaurant_id": "rest_123",
        "item_id": "item_1",
        "name": "Pizza",
        "description": "Delicious pizza",
        "price": "12.99",
        "category": "main",
        "availability": True,
        "allergens": [],
    }
    created_item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_1",
        name="Pizza",
        description="Delicious pizza",
        price=Decimal("12.99"),
        category="main",
        availability=True,
        allergens=[],
    )
    mock_repository.create.return_value = created_item

    # Act - API key authorized for rest_123
    response = client.post(
        "/menus/rest_123/items",
        json=item_data,
        headers={"X-API-Key": "key-rest-123"},
    )

    # Assert
    assert response.status_code == 201
    mock_repository.create.assert_called_once()


@pytest.mark.component
def test_post_item_with_unauthorized_key_returns_403(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test POST item returns 403 when API key doesn't have permission for restaurant."""
    # Arrange
    item_data = {
        "restaurant_id": "rest_456",
        "item_id": "item_1",
        "name": "Pizza",
        "description": "Delicious pizza",
        "price": "12.99",
        "category": "main",
        "availability": True,
        "allergens": [],
    }

    # Act - API key NOT authorized for rest_456 (only authorized for rest_123)
    response = client.post(
        "/menus/rest_456/items",
        json=item_data,
        headers={"X-API-Key": "key-rest-123"},
    )

    # Assert
    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()
    # Repository should not be called
    mock_repository.create.assert_not_called()


# GET /menus/{restaurant_id}/items/{item_id} - Get single item authorization tests


@pytest.mark.component
def test_get_item_with_authorized_key_succeeds(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET single item succeeds when API key has permission for restaurant."""
    # Arrange
    item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_1",
        name="Pizza",
        description="Delicious pizza",
        price=Decimal("12.99"),
        category="main",
        availability=True,
        allergens=[],
    )
    mock_repository.get.return_value = item

    # Act - API key authorized for rest_123
    response = client.get(
        "/menus/rest_123/items/item_1",
        headers={"X-API-Key": "key-rest-123"},
    )

    # Assert
    assert response.status_code == 200
    mock_repository.get.assert_called_once_with("rest_123", "item_1")


@pytest.mark.component
def test_get_item_with_unauthorized_key_returns_403(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET single item returns 403 when API key doesn't have permission."""
    # Act - API key NOT authorized for rest_456
    response = client.get(
        "/menus/rest_456/items/item_1",
        headers={"X-API-Key": "key-rest-123"},
    )

    # Assert
    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()
    # Repository should not be called
    mock_repository.get.assert_not_called()


# PUT /menus/{restaurant_id}/items/{item_id} - Update item authorization tests


@pytest.mark.component
def test_put_item_with_authorized_key_succeeds(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test PUT item succeeds when API key has permission for restaurant."""
    # Arrange
    item_data = {
        "restaurant_id": "rest_123",
        "item_id": "item_1",
        "name": "Updated Pizza",
        "description": "Updated description",
        "price": "15.99",
        "category": "main",
        "availability": True,
        "allergens": [],
    }
    updated_item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_1",
        name="Updated Pizza",
        description="Updated description",
        price=Decimal("15.99"),
        category="main",
        availability=True,
        allergens=[],
    )
    mock_repository.update.return_value = updated_item

    # Act - API key authorized for rest_123
    response = client.put(
        "/menus/rest_123/items/item_1",
        json=item_data,
        headers={"X-API-Key": "key-rest-123"},
    )

    # Assert
    assert response.status_code == 200
    mock_repository.update.assert_called_once()


@pytest.mark.component
def test_put_item_with_unauthorized_key_returns_403(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test PUT item returns 403 when API key doesn't have permission."""
    # Arrange
    item_data = {
        "restaurant_id": "rest_456",
        "item_id": "item_1",
        "name": "Updated Pizza",
        "description": "Updated description",
        "price": "15.99",
        "category": "main",
        "availability": True,
        "allergens": [],
    }

    # Act - API key NOT authorized for rest_456
    response = client.put(
        "/menus/rest_456/items/item_1",
        json=item_data,
        headers={"X-API-Key": "key-rest-123"},
    )

    # Assert
    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()
    # Repository should not be called
    mock_repository.update.assert_not_called()


# DELETE /menus/{restaurant_id}/items/{item_id} - Delete item authorization tests


@pytest.mark.component
def test_delete_item_with_authorized_key_succeeds(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test DELETE item succeeds when API key has permission for restaurant."""
    # Arrange
    mock_repository.delete.return_value = True

    # Act - API key authorized for rest_123
    response = client.delete(
        "/menus/rest_123/items/item_1",
        headers={"X-API-Key": "key-rest-123"},
    )

    # Assert
    assert response.status_code == 204
    mock_repository.delete.assert_called_once_with("rest_123", "item_1")


@pytest.mark.component
def test_delete_item_with_unauthorized_key_returns_403(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test DELETE item returns 403 when API key doesn't have permission."""
    # Act - API key NOT authorized for rest_456
    response = client.delete(
        "/menus/rest_456/items/item_1",
        headers={"X-API-Key": "key-rest-123"},
    )

    # Assert
    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()
    # Repository should not be called
    mock_repository.delete.assert_not_called()


# Test that authentication (401) is checked before authorization (403)


@pytest.mark.component
def test_invalid_key_returns_401_not_403(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test that invalid API key returns 401, not 403, even if restaurant check would fail."""
    # Act - Invalid API key (not in valid_keys set)
    response = client.get(
        "/menus/rest_123/items",
        headers={"X-API-Key": "totally-invalid-key"},
    )

    # Assert - Should get 401 (authentication failed) not 403 (authorization failed)
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key"}
    # Repository should not be called
    mock_repository.list_by_restaurant.assert_not_called()
