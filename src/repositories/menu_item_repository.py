"""MenuItemRepository - Data access layer for menu items in DynamoDB.

This repository handles all DynamoDB operations for menu items, including:
- Creating new menu items
- Retrieving menu items by key
- Listing all items for a restaurant
- Updating existing items
- Deleting items

All operations are instrumented with OpenTelemetry for observability.
"""

from decimal import Decimal
from typing import Any

from boto3.dynamodb.conditions import Key

from src.models.menu_item_model import MenuItem
from src.observability.tracing import traced


class MenuItemRepository:
    """Repository for menu item CRUD operations in DynamoDB.

    This repository follows the repository pattern to abstract DynamoDB
    operations and provide a clean interface for working with menu items.

    Attributes:
        table: The DynamoDB table resource for menu items
    """

    def __init__(self, table: Any) -> None:
        """Initialize the repository with a DynamoDB table.

        Args:
            table: boto3 DynamoDB table resource
        """
        self.table = table

    @traced("create")
    def create(self, item: MenuItem) -> MenuItem:
        """Create a new menu item in DynamoDB.

        Args:
            item: The MenuItem to create

        Returns:
            The created MenuItem
        """
        item_dict = item.model_dump()
        # Convert Decimal to string for DynamoDB storage
        item_dict["price"] = str(item_dict["price"])

        self.table.put_item(Item=item_dict)

        return item

    @traced("get")
    def get(self, restaurant_id: str, item_id: str) -> MenuItem | None:
        """Retrieve a menu item by restaurant_id and item_id.

        Args:
            restaurant_id: The restaurant identifier
            item_id: The menu item identifier

        Returns:
            The MenuItem if found, None otherwise
        """
        response = self.table.get_item(Key={"restaurant_id": restaurant_id, "item_id": item_id})

        if "Item" not in response:
            return None

        return self._item_from_dynamodb(response["Item"])

    @traced("list_by_restaurant")
    def list_by_restaurant(self, restaurant_id: str) -> list[MenuItem]:
        """List all menu items for a specific restaurant.

        Args:
            restaurant_id: The restaurant identifier

        Returns:
            List of MenuItems for the restaurant (empty list if none found)
        """
        response = self.table.query(KeyConditionExpression=Key("restaurant_id").eq(restaurant_id))

        items = response.get("Items", [])
        return [self._item_from_dynamodb(item) for item in items]

    @traced("update")
    def update(self, item: MenuItem) -> MenuItem | None:
        """Update an existing menu item.

        Args:
            item: The MenuItem with updated values

        Returns:
            The updated MenuItem if it exists, None otherwise
        """
        # Check if item exists first
        existing = self.get(item.restaurant_id, item.item_id)
        if existing is None:
            return None

        # Update the item (put_item overwrites)
        item_dict = item.model_dump()
        item_dict["price"] = str(item_dict["price"])

        self.table.put_item(Item=item_dict)

        return item

    @traced("delete")
    def delete(self, restaurant_id: str, item_id: str) -> bool:
        """Delete a menu item.

        Args:
            restaurant_id: The restaurant identifier
            item_id: The menu item identifier

        Returns:
            True if the item was deleted, False if it didn't exist
        """
        # Check if item exists first
        existing = self.get(restaurant_id, item_id)
        if existing is None:
            return False

        self.table.delete_item(Key={"restaurant_id": restaurant_id, "item_id": item_id})

        return True

    def _item_from_dynamodb(self, item_dict: dict[str, Any]) -> MenuItem:
        """Convert a DynamoDB item dict to a MenuItem model.

        Args:
            item_dict: Dictionary from DynamoDB

        Returns:
            MenuItem instance
        """
        # Convert price string back to Decimal
        if "price" in item_dict:
            item_dict["price"] = Decimal(item_dict["price"])

        return MenuItem(**item_dict)
