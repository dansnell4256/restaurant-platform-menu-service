"""Component tests for POST category API endpoint.

This test verifies the FastAPI endpoint for creating categories:
- POST /menus/{restaurant_id}/categories - Create a new category
- Requires X-API-Key header for authentication
- Returns 201 with created category on success
- Returns 401 if API key is missing or invalid
- Returns 400 if restaurant_id in body doesn't match path
- Returns 422 if request body fails validation
"""

from collections.abc import Generator
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.api.categories import create_app
from src.models.category_model import Category
from src.security.api_key_validator import APIKeyValidator


@pytest.fixture
def mock_repository() -> Mock:
    """Create a mock CategoryRepository for testing."""
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
def test_post_category_without_api_key_returns_401(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test POST /menus/{restaurant_id}/categories returns 401 without API key."""
    # Arrange
    category_data = {
        "restaurant_id": "rest_123",
        "category_id": "cat_1",
        "name": "Appetizers",
        "display_order": 1,
        "parent_category": None,
    }

    # Act - No X-API-Key header
    response = client.post("/menus/rest_123/categories", json=category_data)

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key"}
    # Repository should not be called
    mock_repository.create.assert_not_called()


@pytest.mark.component
def test_post_category_with_invalid_api_key_returns_401(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test POST /menus/{restaurant_id}/categories returns 401 with invalid API key."""
    # Arrange
    category_data = {
        "restaurant_id": "rest_123",
        "category_id": "cat_1",
        "name": "Appetizers",
        "display_order": 1,
        "parent_category": None,
    }

    # Act - Invalid API key
    response = client.post(
        "/menus/rest_123/categories",
        json=category_data,
        headers={"X-API-Key": "invalid-key"},
    )

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key"}
    # Repository should not be called
    mock_repository.create.assert_not_called()


@pytest.mark.component
def test_post_category_creates_new_category(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test POST /menus/{restaurant_id}/categories creates new category."""
    # Arrange
    category_data = {
        "restaurant_id": "rest_123",
        "category_id": "cat_1",
        "name": "Appetizers",
        "display_order": 1,
        "parent_category": None,
    }

    created_category = Category(
        restaurant_id="rest_123",
        category_id="cat_1",
        name="Appetizers",
        display_order=1,
        parent_category=None,
    )
    mock_repository.create.return_value = created_category

    # Act - Valid API key
    response = client.post(
        "/menus/rest_123/categories",
        json=category_data,
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 201
    json_response = response.json()
    assert json_response["restaurant_id"] == "rest_123"
    assert json_response["category_id"] == "cat_1"
    assert json_response["name"] == "Appetizers"
    assert json_response["display_order"] == 1
    assert json_response["parent_category"] is None

    # Verify repository was called with correct data
    mock_repository.create.assert_called_once()
    call_args = mock_repository.create.call_args[0][0]
    assert isinstance(call_args, Category)
    assert call_args.restaurant_id == "rest_123"
    assert call_args.category_id == "cat_1"
    assert call_args.name == "Appetizers"


@pytest.mark.component
def test_post_category_validates_restaurant_id_matches_path(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test POST endpoint validates restaurant_id in body matches path parameter."""
    # Arrange - restaurant_id in body doesn't match path
    category_data = {
        "restaurant_id": "rest_456",  # Different from path
        "category_id": "cat_1",
        "name": "Appetizers",
        "display_order": 1,
        "parent_category": None,
    }

    # Act - Valid API key
    response = client.post(
        "/menus/rest_123/categories",
        json=category_data,
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 400
    assert "restaurant_id" in response.json()["detail"].lower()
    # Repository should not be called
    mock_repository.create.assert_not_called()


@pytest.mark.component
def test_post_category_with_incomplete_payload_returns_422(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test POST endpoint rejects incomplete payload missing required fields."""
    # Arrange - Missing required 'name' field
    category_data = {
        "restaurant_id": "rest_123",
        "category_id": "cat_1",
        "display_order": 1,
        "parent_category": None,
    }

    # Act - Valid API key but incomplete data
    response = client.post(
        "/menus/rest_123/categories",
        json=category_data,
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 422  # Unprocessable Entity (validation error)
    # Repository should not be called
    mock_repository.create.assert_not_called()


@pytest.mark.component
def test_post_category_with_parent_category(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test POST endpoint creates category with parent_category."""
    # Arrange
    category_data = {
        "restaurant_id": "rest_123",
        "category_id": "cat_veg_pasta",
        "name": "Vegetarian Pasta",
        "display_order": 5,
        "parent_category": "cat_pasta",
    }

    created_category = Category(
        restaurant_id="rest_123",
        category_id="cat_veg_pasta",
        name="Vegetarian Pasta",
        display_order=5,
        parent_category="cat_pasta",
    )
    mock_repository.create.return_value = created_category

    # Act - Valid API key
    response = client.post(
        "/menus/rest_123/categories",
        json=category_data,
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 201
    json_response = response.json()
    assert json_response["parent_category"] == "cat_pasta"
    assert json_response["name"] == "Vegetarian Pasta"
