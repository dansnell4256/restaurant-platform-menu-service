"""FastAPI endpoints for menu item operations.

This module provides REST API endpoints for managing restaurant menu items:
- GET /restaurants/{restaurant_id}/items - List all items for a restaurant

All endpoints require API key authentication via X-API-Key header.
"""

from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

from src.models.menu_item import MenuItem
from src.repositories.menu_item_repository import MenuItemRepository
from src.security.api_key_validator import APIKeyValidator


def create_app(
    repository: MenuItemRepository,
    api_key_validator: APIKeyValidator,
) -> FastAPI:
    """Create and configure FastAPI application.

    Args:
        repository: MenuItemRepository for data access
        api_key_validator: APIKeyValidator for authentication

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Restaurant Menu Service",
        description="Microservice for managing restaurant menu items",
        version="0.1.0",
    )

    async def verify_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
        """Verify API key from X-API-Key header.

        Args:
            x_api_key: API key from request header

        Raises:
            HTTPException: 401 if API key is missing or invalid
        """
        if not api_key_validator.is_valid(x_api_key):
            raise HTTPException(status_code=401, detail="Missing or invalid API key")

    @app.get(
        "/restaurants/{restaurant_id}/items",
        response_model=list[MenuItem],
        dependencies=[Depends(verify_api_key)],
    )
    async def get_items(restaurant_id: str) -> list[MenuItem]:
        """Get all menu items for a restaurant.

        Args:
            restaurant_id: The restaurant identifier

        Returns:
            List of menu items (empty list if none found)
        """
        return repository.list_by_restaurant(restaurant_id)

    return app
