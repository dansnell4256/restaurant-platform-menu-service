"""Component tests for CategoryRepository.

Tests the CategoryRepository with mocked DynamoDB using moto.
Covers list_by_restaurant operation for categories.
"""

from typing import Any

import boto3
import pytest
from moto import mock_aws

from src.models.category_model import Category
from src.repositories.category_repository import CategoryRepository


@pytest.fixture
def dynamodb_table() -> Any:
    """Create a mocked DynamoDB table for testing."""
    with mock_aws():
        # Create DynamoDB resource
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        # Create table
        table = dynamodb.create_table(
            TableName="categories",
            KeySchema=[
                {"AttributeName": "restaurant_id", "KeyType": "HASH"},
                {"AttributeName": "category_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "restaurant_id", "AttributeType": "S"},
                {"AttributeName": "category_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        yield table


@pytest.fixture
def repository(dynamodb_table: Any) -> CategoryRepository:
    """Create a CategoryRepository with mocked DynamoDB table."""
    return CategoryRepository(table=dynamodb_table)


@pytest.mark.component
def test_list_categories_for_restaurant(
    repository: CategoryRepository,
    dynamodb_table: Any,
) -> None:
    """Test listing all categories for a specific restaurant."""
    # Arrange - Add categories to DynamoDB
    dynamodb_table.put_item(
        Item={
            "restaurant_id": "rest_123",
            "category_id": "cat_1",
            "name": "Appetizers",
            "display_order": 1,
            "parent_category": None,
        }
    )
    dynamodb_table.put_item(
        Item={
            "restaurant_id": "rest_123",
            "category_id": "cat_2",
            "name": "Main Courses",
            "display_order": 2,
            "parent_category": None,
        }
    )

    # Act
    categories = repository.list_by_restaurant("rest_123")

    # Assert
    assert len(categories) == 2
    assert all(isinstance(cat, Category) for cat in categories)
    assert categories[0].restaurant_id == "rest_123"
    assert categories[0].name in ["Appetizers", "Main Courses"]


@pytest.mark.component
def test_list_categories_for_restaurant_with_no_categories(
    repository: CategoryRepository,
) -> None:
    """Test listing categories for a restaurant with no categories."""
    # Act
    categories = repository.list_by_restaurant("rest_nonexistent")

    # Assert
    assert categories == []


@pytest.mark.component
def test_list_categories_ordered_by_display_order(
    repository: CategoryRepository,
    dynamodb_table: Any,
) -> None:
    """Test that categories are returned in display_order."""
    # Arrange - Add categories in non-sequential order
    dynamodb_table.put_item(
        Item={
            "restaurant_id": "rest_123",
            "category_id": "cat_3",
            "name": "Desserts",
            "display_order": 10,
            "parent_category": None,
        }
    )
    dynamodb_table.put_item(
        Item={
            "restaurant_id": "rest_123",
            "category_id": "cat_1",
            "name": "Appetizers",
            "display_order": 1,
            "parent_category": None,
        }
    )
    dynamodb_table.put_item(
        Item={
            "restaurant_id": "rest_123",
            "category_id": "cat_2",
            "name": "Main Courses",
            "display_order": 5,
            "parent_category": None,
        }
    )

    # Act
    categories = repository.list_by_restaurant("rest_123")

    # Assert
    assert len(categories) == 3
    assert categories[0].name == "Appetizers"
    assert categories[0].display_order == 1
    assert categories[1].name == "Main Courses"
    assert categories[1].display_order == 5
    assert categories[2].name == "Desserts"
    assert categories[2].display_order == 10


@pytest.mark.component
def test_list_categories_with_parent_category(
    repository: CategoryRepository,
    dynamodb_table: Any,
) -> None:
    """Test listing categories that have parent_category relationships."""
    # Arrange
    dynamodb_table.put_item(
        Item={
            "restaurant_id": "rest_123",
            "category_id": "cat_parent",
            "name": "Pasta",
            "display_order": 5,
            "parent_category": None,
        }
    )
    dynamodb_table.put_item(
        Item={
            "restaurant_id": "rest_123",
            "category_id": "cat_child",
            "name": "Vegetarian Pasta",
            "display_order": 6,
            "parent_category": "cat_parent",
        }
    )

    # Act
    categories = repository.list_by_restaurant("rest_123")

    # Assert
    assert len(categories) == 2
    parent = next(c for c in categories if c.category_id == "cat_parent")
    child = next(c for c in categories if c.category_id == "cat_child")

    assert parent.parent_category is None
    assert child.parent_category == "cat_parent"


@pytest.mark.component
def test_create_category(
    repository: CategoryRepository,
    dynamodb_table: Any,
) -> None:
    """Test creating a new category."""
    # Arrange
    category = Category(
        restaurant_id="rest_123",
        category_id="cat_1",
        name="Appetizers",
        display_order=1,
        parent_category=None,
    )

    # Act
    result = repository.create(category)

    # Assert
    assert result.restaurant_id == "rest_123"
    assert result.category_id == "cat_1"
    assert result.name == "Appetizers"
    assert result.display_order == 1
    assert result.parent_category is None

    # Verify it was actually stored in DynamoDB
    response = dynamodb_table.get_item(Key={"restaurant_id": "rest_123", "category_id": "cat_1"})
    assert "Item" in response
    assert response["Item"]["name"] == "Appetizers"


@pytest.mark.component
def test_create_category_with_parent(
    repository: CategoryRepository,
    dynamodb_table: Any,
) -> None:
    """Test creating a category with a parent_category."""
    # Arrange
    category = Category(
        restaurant_id="rest_123",
        category_id="cat_2",
        name="Vegetarian Pasta",
        display_order=5,
        parent_category="cat_pasta",
    )

    # Act
    result = repository.create(category)

    # Assert
    assert result.parent_category == "cat_pasta"

    # Verify it was stored with parent_category
    response = dynamodb_table.get_item(Key={"restaurant_id": "rest_123", "category_id": "cat_2"})
    assert response["Item"]["parent_category"] == "cat_pasta"


@pytest.mark.component
def test_create_category_preserves_all_fields(
    repository: CategoryRepository,
    dynamodb_table: Any,
) -> None:
    """Test that create preserves all category fields."""
    # Arrange
    category = Category(
        restaurant_id="rest_456",
        category_id="cat_desserts",
        name="Desserts",
        display_order=10,
        parent_category="cat_sweets",
    )

    # Act
    result = repository.create(category)

    # Assert - Check returned object
    assert result.restaurant_id == "rest_456"
    assert result.category_id == "cat_desserts"
    assert result.name == "Desserts"
    assert result.display_order == 10
    assert result.parent_category == "cat_sweets"

    # Assert - Check stored in DynamoDB
    response = dynamodb_table.get_item(
        Key={"restaurant_id": "rest_456", "category_id": "cat_desserts"}
    )
    stored_item = response["Item"]
    assert stored_item["restaurant_id"] == "rest_456"
    assert stored_item["category_id"] == "cat_desserts"
    assert stored_item["name"] == "Desserts"
    assert stored_item["display_order"] == 10
    assert stored_item["parent_category"] == "cat_sweets"
