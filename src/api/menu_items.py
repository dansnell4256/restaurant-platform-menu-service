"""FastAPI endpoints for menu item operations.

This module provides REST API endpoints for managing restaurant menu items:
- GET /menus/{restaurant_id}/items - List all items for a restaurant
- GET /menus/{restaurant_id}/items/{item_id} - Get a specific menu item
- POST /menus/{restaurant_id}/items - Create a new menu item
- PUT /menus/{restaurant_id}/items/{item_id} - Update an existing menu item
- DELETE /menus/{restaurant_id}/items/{item_id} - Delete a menu item

All endpoints require API key authentication via X-API-Key header.
"""

from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status

from src.models.menu_item_model import MenuItem
from src.observability.tracing import traced
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
        "/menus/{restaurant_id}/items",
        response_model=list[MenuItem],
        dependencies=[Depends(verify_api_key)],
    )
    @traced("get_items")
    async def get_items(restaurant_id: str) -> list[MenuItem]:
        """Get all menu items for a restaurant.

        Args:
            restaurant_id: The restaurant identifier

        Returns:
            List of menu items (empty list if none found)
        """
        return repository.list_by_restaurant(restaurant_id)

    @app.get(
        "/menus/{restaurant_id}/items/{item_id}",
        response_model=MenuItem,
        dependencies=[Depends(verify_api_key)],
    )
    @traced("get_item")
    async def get_item(restaurant_id: str, item_id: str) -> MenuItem:
        """Get a specific menu item.

        Args:
            restaurant_id: The restaurant identifier
            item_id: The item identifier

        Returns:
            The menu item

        Raises:
            HTTPException: 404 if item is not found
        """
        item = repository.get(restaurant_id, item_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item {item_id} not found for restaurant {restaurant_id}",
            )
        return item

    @app.post(
        "/menus/{restaurant_id}/items",
        response_model=MenuItem,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(verify_api_key)],
    )
    @traced("create_item")
    async def create_item(restaurant_id: str, item: MenuItem) -> MenuItem:
        """Create a new menu item for a restaurant.

        Args:
            restaurant_id: The restaurant identifier from URL path
            item: The menu item to create

        Returns:
            The created menu item

        Raises:
            HTTPException: 400 if restaurant_id in body doesn't match path
        """
        # Validate restaurant_id in body matches path parameter
        if item.restaurant_id != restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"restaurant_id in body ({item.restaurant_id}) does not match path parameter ({restaurant_id})",
            )

        return repository.create(item)

    @app.put(
        "/menus/{restaurant_id}/items/{item_id}",
        response_model=MenuItem,
        dependencies=[Depends(verify_api_key)],
    )
    @traced("update_item")
    async def update_item(restaurant_id: str, item_id: str, item: MenuItem) -> MenuItem:
        """Update an existing menu item.

        Args:
            restaurant_id: The restaurant identifier from URL path
            item_id: The item identifier from URL path
            item: The updated menu item data

        Returns:
            The updated menu item

        Raises:
            HTTPException: 400 if restaurant_id or item_id in body doesn't match path
            HTTPException: 404 if item is not found
        """
        # Validate restaurant_id in body matches path parameter
        if item.restaurant_id != restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"restaurant_id in body ({item.restaurant_id}) does not match path parameter ({restaurant_id})",
            )

        # Validate item_id in body matches path parameter
        if item.item_id != item_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"item_id in body ({item.item_id}) does not match path parameter ({item_id})",
            )

        updated_item = repository.update(item)
        if updated_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item {item_id} not found for restaurant {restaurant_id}",
            )
        return updated_item

    @app.delete(
        "/menus/{restaurant_id}/items/{item_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        dependencies=[Depends(verify_api_key)],
    )
    @traced("delete_item")
    async def delete_item(restaurant_id: str, item_id: str) -> None:
        """Delete a menu item.

        Args:
            restaurant_id: The restaurant identifier from URL path
            item_id: The item identifier from URL path

        Raises:
            HTTPException: 404 if item is not found
        """
        deleted = repository.delete(restaurant_id, item_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item {item_id} not found for restaurant {restaurant_id}",
            )

    return app
