"""Unit tests for Category model.

Tests the Category pydantic model for menu organization including:
- Required fields validation (restaurant_id, category_id, name, display_order)
- Optional parent_category field for hierarchy
- Proper serialization to/from dict
- Field validation rules
"""

import pytest
from pydantic import ValidationError

from src.models.category_model import Category


@pytest.mark.unit
def test_category_with_required_fields_only() -> None:
    """Test creating a category with only required fields."""
    # Arrange & Act
    category = Category(
        restaurant_id="rest_123",
        category_id="cat_1",
        name="Appetizers",
        display_order=1,
    )

    # Assert
    assert category.restaurant_id == "rest_123"
    assert category.category_id == "cat_1"
    assert category.name == "Appetizers"
    assert category.display_order == 1
    assert category.parent_category is None


@pytest.mark.unit
def test_category_with_all_fields() -> None:
    """Test creating a category with all fields including parent_category."""
    # Arrange & Act
    category = Category(
        restaurant_id="rest_123",
        category_id="cat_2",
        name="Vegetarian Pasta",
        display_order=5,
        parent_category="cat_1",
    )

    # Assert
    assert category.restaurant_id == "rest_123"
    assert category.category_id == "cat_2"
    assert category.name == "Vegetarian Pasta"
    assert category.display_order == 5
    assert category.parent_category == "cat_1"


@pytest.mark.unit
def test_category_missing_required_fields() -> None:
    """Test that missing required fields raises ValidationError."""
    # Act & Assert - Missing name
    with pytest.raises(ValidationError) as exc_info:
        Category(
            restaurant_id="rest_123",
            category_id="cat_1",
            display_order=1,
        )  # type: ignore[call-arg]

    # Verify the error is about the missing 'name' field
    assert "name" in str(exc_info.value)


@pytest.mark.unit
def test_category_empty_name_is_invalid() -> None:
    """Test that empty category name is invalid."""
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        Category(
            restaurant_id="rest_123",
            category_id="cat_1",
            name="",
            display_order=1,
        )

    # Verify validation error for name
    assert "name" in str(exc_info.value).lower()


@pytest.mark.unit
def test_category_display_order_must_be_non_negative() -> None:
    """Test that display_order must be >= 0."""
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        Category(
            restaurant_id="rest_123",
            category_id="cat_1",
            name="Desserts",
            display_order=-1,
        )

    # Verify validation error for display_order
    assert "display_order" in str(exc_info.value).lower()


@pytest.mark.unit
def test_category_to_dict() -> None:
    """Test serialization of category to dictionary."""
    # Arrange
    category = Category(
        restaurant_id="rest_123",
        category_id="cat_1",
        name="Main Courses",
        display_order=2,
        parent_category="cat_parent",
    )

    # Act
    category_dict = category.model_dump()

    # Assert
    assert category_dict == {
        "restaurant_id": "rest_123",
        "category_id": "cat_1",
        "name": "Main Courses",
        "display_order": 2,
        "parent_category": "cat_parent",
    }


@pytest.mark.unit
def test_category_from_dict() -> None:
    """Test deserialization of category from dictionary."""
    # Arrange
    category_dict = {
        "restaurant_id": "rest_456",
        "category_id": "cat_3",
        "name": "Beverages",
        "display_order": 10,
        "parent_category": None,
    }

    # Act
    category = Category(**category_dict)  # type: ignore[arg-type]

    # Assert
    assert category.restaurant_id == "rest_456"
    assert category.category_id == "cat_3"
    assert category.name == "Beverages"
    assert category.display_order == 10
    assert category.parent_category is None
