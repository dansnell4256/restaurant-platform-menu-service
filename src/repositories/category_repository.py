"""CategoryRepository - Data access layer for categories in DynamoDB.

This repository handles all DynamoDB operations for categories, including:
- Listing all categories for a restaurant (sorted by display_order)

All operations are instrumented with OpenTelemetry for observability.
"""

from typing import Any

from boto3.dynamodb.conditions import Key

from src.models.category_model import Category
from src.observability.tracing import traced


class CategoryRepository:
    """Repository for category operations in DynamoDB.

    This repository follows the repository pattern to abstract DynamoDB
    operations and provide a clean interface for working with categories.

    Attributes:
        table: The DynamoDB table resource for categories
    """

    def __init__(self, table: Any) -> None:
        """Initialize the repository with a DynamoDB table.

        Args:
            table: boto3 DynamoDB table resource
        """
        self.table = table

    @traced("create")
    def create(self, category: Category) -> Category:
        """Create a new category in DynamoDB.

        Args:
            category: The Category to create

        Returns:
            The created Category
        """
        category_dict = category.model_dump()

        self.table.put_item(Item=category_dict)

        return category

    @traced("list_by_restaurant")
    def list_by_restaurant(self, restaurant_id: str) -> list[Category]:
        """List all categories for a specific restaurant, sorted by display_order.

        Args:
            restaurant_id: The restaurant identifier

        Returns:
            List of Categories for the restaurant, sorted by display_order (empty list if none found)
        """
        response = self.table.query(KeyConditionExpression=Key("restaurant_id").eq(restaurant_id))

        items = response.get("Items", [])
        categories = [self._category_from_dynamodb(item) for item in items]

        # Sort by display_order for consistent presentation
        categories.sort(key=lambda c: c.display_order)

        return categories

    def _category_from_dynamodb(self, item_dict: dict[str, Any]) -> Category:
        """Convert a DynamoDB item dict to a Category model.

        Args:
            item_dict: Dictionary from DynamoDB

        Returns:
            Category instance
        """
        # DynamoDB stores None as absent keys, so we handle that
        if "parent_category" not in item_dict or item_dict["parent_category"] is None:
            item_dict["parent_category"] = None

        return Category(**item_dict)
