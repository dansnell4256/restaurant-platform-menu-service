"""Category model for menu organization.

Categories provide a way to organize and structure menu items for display purposes.
They support hierarchy through parent_category and ordering through display_order.

This is separate from the 'category' string field on MenuItem - Categories are for
UI/presentation organization while MenuItem.category is a simple string tag.
"""

from pydantic import BaseModel, Field


class Category(BaseModel):
    """Category model for organizing menu items.

    Categories help structure menus for display in restaurant admin interfaces
    and customer-facing menu applications. They support hierarchical organization
    (e.g., "Pasta" -> "Vegetarian Pasta") and explicit display ordering.

    Attributes:
        restaurant_id: The restaurant this category belongs to
        category_id: Unique identifier for this category
        name: Display name for the category (e.g., "Appetizers", "Main Courses")
        display_order: Integer for sorting categories in display (lower numbers first)
        parent_category: Optional category_id of parent for hierarchical organization
    """

    restaurant_id: str = Field(..., min_length=1, description="Restaurant identifier")
    category_id: str = Field(..., min_length=1, description="Category identifier")
    name: str = Field(..., min_length=1, description="Category display name")
    display_order: int = Field(..., ge=0, description="Display order (0 or greater)")
    parent_category: str | None = Field(
        None,
        description="Parent category ID for hierarchical structure",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "restaurant_id": "rest_123",
                    "category_id": "cat_1",
                    "name": "Appetizers",
                    "display_order": 1,
                    "parent_category": None,
                },
                {
                    "restaurant_id": "rest_123",
                    "category_id": "cat_2",
                    "name": "Vegetarian Pasta",
                    "display_order": 5,
                    "parent_category": "cat_pasta",
                },
            ]
        }
    }
