"""Component tests for MenuItemRepository.

This test explains what the MenuItemRepository should do:
- Create menu items in DynamoDB
- Retrieve menu items by restaurant_id and item_id
- List all menu items for a restaurant
- Update existing menu items
- Delete menu items
- Handle items that don't exist gracefully
"""

from collections.abc import Generator
from decimal import Decimal
from typing import Any

import boto3
import pytest
from moto import mock_aws

from src.models.menu_item_model import MenuItem
from src.repositories.menu_item_repository import MenuItemRepository


@pytest.fixture
def dynamodb_table() -> Generator[Any, None, None]:
    """Create a mocked DynamoDB table for testing."""
    with mock_aws():
        # Create DynamoDB client
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        # Create table
        table = dynamodb.create_table(
            TableName="menu-items",
            KeySchema=[
                {"AttributeName": "restaurant_id", "KeyType": "HASH"},  # Partition key
                {"AttributeName": "item_id", "KeyType": "RANGE"},  # Sort key
            ],
            AttributeDefinitions=[
                {"AttributeName": "restaurant_id", "AttributeType": "S"},
                {"AttributeName": "item_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        yield table


@pytest.fixture
def repository(dynamodb_table: Any) -> MenuItemRepository:
    """Create MenuItemRepository with mocked DynamoDB table."""
    return MenuItemRepository(table=dynamodb_table)


@pytest.mark.component
def test_create_menu_item(repository: MenuItemRepository) -> None:
    """Test creating a new menu item in DynamoDB."""
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

    created_item = repository.create(item)

    assert created_item.restaurant_id == "rest_123"
    assert created_item.item_id == "item_456"
    assert created_item.name == "Margherita Pizza"
    assert created_item.price == Decimal("12.99")


@pytest.mark.component
def test_get_menu_item(repository: MenuItemRepository) -> None:
    """Test retrieving a menu item by restaurant_id and item_id."""
    # First create an item
    item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_456",
        name="Margherita Pizza",
        price=Decimal("12.99"),
    )
    repository.create(item)

    # Now retrieve it
    retrieved_item = repository.get("rest_123", "item_456")

    assert retrieved_item is not None
    assert retrieved_item.restaurant_id == "rest_123"
    assert retrieved_item.item_id == "item_456"
    assert retrieved_item.name == "Margherita Pizza"
    assert retrieved_item.price == Decimal("12.99")


@pytest.mark.component
def test_get_nonexistent_menu_item(repository: MenuItemRepository) -> None:
    """Test that getting a non-existent item returns None."""
    retrieved_item = repository.get("rest_999", "item_999")

    assert retrieved_item is None


@pytest.mark.component
def test_list_menu_items_for_restaurant(repository: MenuItemRepository) -> None:
    """Test listing all menu items for a specific restaurant."""
    # Create multiple items for the same restaurant
    items = [
        MenuItem(
            restaurant_id="rest_123",
            item_id="item_001",
            name="Margherita Pizza",
            price=Decimal("12.99"),
        ),
        MenuItem(
            restaurant_id="rest_123",
            item_id="item_002",
            name="Pepperoni Pizza",
            price=Decimal("14.99"),
        ),
        MenuItem(
            restaurant_id="rest_123",
            item_id="item_003",
            name="Caesar Salad",
            price=Decimal("8.99"),
        ),
    ]

    for item in items:
        repository.create(item)

    # Create an item for a different restaurant (should not be included)
    repository.create(
        MenuItem(
            restaurant_id="rest_999",
            item_id="item_999",
            name="Other Restaurant Item",
            price=Decimal("10.00"),
        )
    )

    # List items for rest_123
    retrieved_items = repository.list_by_restaurant("rest_123")

    assert len(retrieved_items) == 3
    item_ids = {item.item_id for item in retrieved_items}
    assert item_ids == {"item_001", "item_002", "item_003"}


@pytest.mark.component
def test_list_menu_items_for_restaurant_with_no_items(
    repository: MenuItemRepository,
) -> None:
    """Test listing items for a restaurant that has no items returns empty list."""
    retrieved_items = repository.list_by_restaurant("rest_999")

    assert retrieved_items == []


@pytest.mark.component
def test_update_menu_item(repository: MenuItemRepository) -> None:
    """Test updating an existing menu item."""
    # Create an item
    original_item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_456",
        name="Margherita Pizza",
        price=Decimal("12.99"),
        availability=True,
    )
    repository.create(original_item)

    # Update the item
    updated_item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_456",
        name="Margherita Pizza (Large)",
        price=Decimal("15.99"),
        availability=False,
        description="Now with extra cheese",
    )
    result = repository.update(updated_item)

    assert result is not None
    assert result.name == "Margherita Pizza (Large)"
    assert result.price == Decimal("15.99")
    assert result.availability is False
    assert result.description == "Now with extra cheese"

    # Verify the update persisted
    retrieved = repository.get("rest_123", "item_456")
    assert retrieved is not None
    assert retrieved.name == "Margherita Pizza (Large)"
    assert retrieved.price == Decimal("15.99")


@pytest.mark.component
def test_update_nonexistent_menu_item(repository: MenuItemRepository) -> None:
    """Test that updating a non-existent item returns None."""
    item = MenuItem(
        restaurant_id="rest_999",
        item_id="item_999",
        name="Nonexistent Item",
        price=Decimal("10.00"),
    )

    result = repository.update(item)

    assert result is None


@pytest.mark.component
def test_delete_menu_item(repository: MenuItemRepository) -> None:
    """Test deleting a menu item."""
    # Create an item
    item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_456",
        name="Margherita Pizza",
        price=Decimal("12.99"),
    )
    repository.create(item)

    # Delete the item
    deleted = repository.delete("rest_123", "item_456")

    assert deleted is True

    # Verify it's gone
    retrieved = repository.get("rest_123", "item_456")
    assert retrieved is None


@pytest.mark.component
def test_delete_nonexistent_menu_item(repository: MenuItemRepository) -> None:
    """Test that deleting a non-existent item returns False."""
    deleted = repository.delete("rest_999", "item_999")

    assert deleted is False


@pytest.mark.component
def test_create_preserves_all_fields(repository: MenuItemRepository) -> None:
    """Test that creating an item preserves all fields including optional ones."""
    item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_456",
        name="Margherita Pizza",
        description="Classic tomato sauce, mozzarella, and fresh basil",
        price=Decimal("12.99"),
        category="pizza",
        availability=False,
        allergens=["dairy", "gluten", "tomato"],
    )

    repository.create(item)
    retrieved = repository.get("rest_123", "item_456")

    assert retrieved is not None
    assert retrieved.description == "Classic tomato sauce, mozzarella, and fresh basil"
    assert retrieved.category == "pizza"
    assert retrieved.availability is False
    assert retrieved.allergens == ["dairy", "gluten", "tomato"]
