"""FastAPI endpoints for category operations.

This module provides REST API endpoints for managing menu categories:
- GET /menus/{restaurant_id}/categories - List all categories for a restaurant

All endpoints require API key authentication via X-API-Key header.
"""

from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

from src.models.category_model import Category
from src.observability.tracing import traced
from src.repositories.category_repository import CategoryRepository
from src.security.api_key_validator import APIKeyValidator


def create_app(
    repository: CategoryRepository,
    api_key_validator: APIKeyValidator,
) -> FastAPI:
    """Create and configure FastAPI application.

    Args:
        repository: CategoryRepository for data access
        api_key_validator: APIKeyValidator for authentication

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Restaurant Menu Service - Categories",
        description="Microservice for managing restaurant menu categories",
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
        "/menus/{restaurant_id}/categories",
        response_model=list[Category],
        dependencies=[Depends(verify_api_key)],
    )
    @traced("get_categories")
    async def get_categories(restaurant_id: str) -> list[Category]:
        """Get all categories for a restaurant.

        Args:
            restaurant_id: The restaurant identifier

        Returns:
            List of categories sorted by display_order (empty list if none found)
        """
        return repository.list_by_restaurant(restaurant_id)

    return app
