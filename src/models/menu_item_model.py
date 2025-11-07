"""MenuItem data model for restaurant menu items.

This model represents a menu item in a restaurant, including pricing,
description, availability, and allergen information.
"""

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class MenuItem(BaseModel):
    """Represents a menu item in a restaurant.

    Attributes:
        restaurant_id: Unique identifier for the restaurant (partition key)
        item_id: Unique identifier for the menu item (sort key)
        name: Display name of the menu item
        description: Optional detailed description of the item
        price: Price in decimal format (must be >= 0)
        category: Optional category/section (e.g., "pizza", "appetizers")
        availability: Whether the item is currently available (default: True)
        allergens: List of allergen information (default: empty list)
    """

    restaurant_id: str = Field(..., description="Restaurant identifier")
    item_id: str = Field(..., description="Menu item identifier")
    name: str = Field(..., min_length=1, description="Menu item name")
    description: str | None = Field(None, description="Item description")
    price: Decimal = Field(..., ge=0, description="Price (must be >= 0)")
    category: str | None = Field(None, description="Menu category")
    availability: bool = Field(True, description="Is item available")
    allergens: list[str] = Field(default_factory=list, description="Allergen list")

    @field_validator("price", mode="before")
    @classmethod
    def validate_price(cls, v: Decimal | float | str | int) -> Decimal:
        """Ensure price is converted to Decimal for precision."""
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "restaurant_id": "rest_123",
                    "item_id": "item_456",
                    "name": "Margherita Pizza",
                    "description": "Classic tomato sauce, mozzarella, and fresh basil",
                    "price": "12.99",
                    "category": "pizza",
                    "availability": True,
                    "allergens": ["dairy", "gluten"],
                }
            ]
        }
    }
