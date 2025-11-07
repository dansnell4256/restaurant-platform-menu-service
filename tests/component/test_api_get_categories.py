"""Component tests for GET categories API endpoint.

This test verifies the FastAPI endpoint for listing categories:
- GET /menus/{restaurant_id}/categories - List all categories for a restaurant
- Requires X-API-Key header for authentication
- Returns 200 with list of categories (empty list if none exist)
- Returns 401 if API key is missing or invalid
- Properly formats Category objects as JSON responses
"""

from collections.abc import Generator
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.api.categories import create_app
from src.models.category import Category
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
def test_get_categories_without_api_key_returns_401(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET /menus/{restaurant_id}/categories returns 401 without API key."""
    # Act - No X-API-Key header
    response = client.get("/menus/rest_123/categories")

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key"}
    # Repository should not be called
    mock_repository.list_by_restaurant.assert_not_called()


@pytest.mark.component
def test_get_categories_with_invalid_api_key_returns_401(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET /menus/{restaurant_id}/categories returns 401 with invalid API key."""
    # Act - Invalid API key
    response = client.get(
        "/menus/rest_123/categories",
        headers={"X-API-Key": "invalid-key"},
    )

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key"}
    # Repository should not be called
    mock_repository.list_by_restaurant.assert_not_called()


@pytest.mark.component
def test_get_categories_returns_empty_list_when_no_categories(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET /menus/{restaurant_id}/categories returns empty list when no categories exist."""
    # Arrange
    mock_repository.list_by_restaurant.return_value = []

    # Act - Valid API key
    response = client.get(
        "/menus/rest_123/categories",
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == []
    mock_repository.list_by_restaurant.assert_called_once_with("rest_123")


@pytest.mark.component
def test_get_categories_returns_list_of_categories(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET /menus/{restaurant_id}/categories returns list of categories."""
    # Arrange
    categories = [
        Category(
            restaurant_id="rest_123",
            category_id="cat_1",
            name="Appetizers",
            display_order=1,
            parent_category=None,
        ),
        Category(
            restaurant_id="rest_123",
            category_id="cat_2",
            name="Main Courses",
            display_order=2,
            parent_category=None,
        ),
    ]
    mock_repository.list_by_restaurant.return_value = categories

    # Act - Valid API key
    response = client.get(
        "/menus/rest_123/categories",
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 2

    # Verify first category
    assert json_response[0]["restaurant_id"] == "rest_123"
    assert json_response[0]["category_id"] == "cat_1"
    assert json_response[0]["name"] == "Appetizers"
    assert json_response[0]["display_order"] == 1
    assert json_response[0]["parent_category"] is None

    # Verify second category
    assert json_response[1]["restaurant_id"] == "rest_123"
    assert json_response[1]["category_id"] == "cat_2"
    assert json_response[1]["name"] == "Main Courses"
    assert json_response[1]["display_order"] == 2

    mock_repository.list_by_restaurant.assert_called_once_with("rest_123")


@pytest.mark.component
def test_get_categories_with_different_restaurant_id(
    client: TestClient,
    mock_repository: Mock,
) -> None:
    """Test GET endpoint works with different restaurant IDs."""
    # Arrange
    mock_repository.list_by_restaurant.return_value = []

    # Act - Valid API key
    response = client.get(
        "/menus/rest_456/categories",
        headers={"X-API-Key": "test-key-456"},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == []
    mock_repository.list_by_restaurant.assert_called_once_with("rest_456")
