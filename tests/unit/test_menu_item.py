"""Unit tests for MenuItem model.

This test explains what the MenuItem model should do:
- Represent a menu item with required fields (restaurant_id, item_id, name, price)
- Support optional fields (description, category, availability, allergens)
- Validate that price is positive
- Validate that required fields are present
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.models.menu_item_model import MenuItem


@pytest.mark.unit
def test_menu_item_with_required_fields_only() -> None:
    """Test creating a MenuItem with only required fields."""
    item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_456",
        name="Margherita Pizza",
        price=Decimal("12.99"),
    )

    assert item.restaurant_id == "rest_123"
    assert item.item_id == "item_456"
    assert item.name == "Margherita Pizza"
    assert item.price == Decimal("12.99")
    assert item.description is None
    assert item.category is None
    assert item.availability is True  # Default should be available
    assert item.allergens == []  # Default should be empty list


@pytest.mark.unit
def test_menu_item_with_all_fields() -> None:
    """Test creating a MenuItem with all fields populated."""
    item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_456",
        name="Margherita Pizza",
        description="Classic tomato sauce, mozzarella, and fresh basil",
        price=Decimal("12.99"),
        category="pizza",
        availability=True,
        allergens=["dairy", "gluten"],
    )

    assert item.restaurant_id == "rest_123"
    assert item.item_id == "item_456"
    assert item.name == "Margherita Pizza"
    assert item.description == "Classic tomato sauce, mozzarella, and fresh basil"
    assert item.price == Decimal("12.99")
    assert item.category == "pizza"
    assert item.availability is True
    assert item.allergens == ["dairy", "gluten"]


@pytest.mark.unit
def test_menu_item_price_must_be_positive() -> None:
    """Test that price validation rejects negative prices."""
    with pytest.raises(ValidationError) as exc_info:
        MenuItem(
            restaurant_id="rest_123",
            item_id="item_456",
            name="Free Pizza",
            price=Decimal("-10.00"),
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("price",) for error in errors)


@pytest.mark.unit
def test_menu_item_price_zero_is_valid() -> None:
    """Test that zero price is valid (for promotional items)."""
    item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_456",
        name="Free Sample",
        price=Decimal("0.00"),
    )

    assert item.price == Decimal("0.00")


@pytest.mark.unit
def test_menu_item_missing_required_fields() -> None:
    """Test that ValidationError is raised when required fields are missing."""
    with pytest.raises(ValidationError) as exc_info:
        MenuItem(restaurant_id="rest_123")  # type: ignore

    errors = exc_info.value.errors()
    error_fields = {error["loc"][0] for error in errors}
    assert "item_id" in error_fields
    assert "name" in error_fields
    assert "price" in error_fields


@pytest.mark.unit
def test_menu_item_empty_name_is_invalid() -> None:
    """Test that empty name is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        MenuItem(
            restaurant_id="rest_123",
            item_id="item_456",
            name="",
            price=Decimal("12.99"),
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("name",) for error in errors)


@pytest.mark.unit
def test_menu_item_to_dict() -> None:
    """Test converting MenuItem to dictionary for DynamoDB storage."""
    item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_456",
        name="Margherita Pizza",
        description="Classic pizza",
        price=Decimal("12.99"),
        category="pizza",
        availability=True,
        allergens=["dairy", "gluten"],
    )

    item_dict = item.model_dump()

    assert item_dict["restaurant_id"] == "rest_123"
    assert item_dict["item_id"] == "item_456"
    assert item_dict["name"] == "Margherita Pizza"
    assert item_dict["description"] == "Classic pizza"
    assert item_dict["price"] == Decimal("12.99")
    assert item_dict["category"] == "pizza"
    assert item_dict["availability"] is True
    assert item_dict["allergens"] == ["dairy", "gluten"]
