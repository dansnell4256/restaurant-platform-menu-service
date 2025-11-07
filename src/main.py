"""Main application entry point for local development.

This module creates and configures the FastAPI application for running locally.
It combines all API endpoints into a single unified application.

For local development, you can run:
    uvicorn src.main:app --reload --port 8000

Or with Python:
    python -m src.main

The API will be available at http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Menu Items: http://localhost:8000/menus/{restaurant_id}/items
- Categories: http://localhost:8000/menus/{restaurant_id}/categories
"""

import os
from typing import Annotated

import boto3
from fastapi import Depends, FastAPI, Header, HTTPException, status

from src.models.category_model import Category
from src.models.menu_item_model import MenuItem
from src.observability.tracing import traced
from src.repositories.category_repository import CategoryRepository
from src.repositories.menu_item_repository import MenuItemRepository
from src.security.api_key_validator import APIKeyValidator

# Global repositories and validator (initialized on startup)
menu_item_repository: MenuItemRepository
category_repository: CategoryRepository
api_key_validator: APIKeyValidator


def get_dynamodb_resource() -> boto3.resources.base.ServiceResource:
    """Get DynamoDB resource based on environment.

    For local development, set DYNAMODB_ENDPOINT environment variable.
    For AWS, leave unset to use default AWS credentials.

    Returns:
        boto3 DynamoDB resource
    """
    endpoint_url = os.getenv("DYNAMODB_ENDPOINT")
    region = os.getenv("AWS_REGION", "us-east-1")

    if endpoint_url:
        # Local DynamoDB (docker or localstack)
        return boto3.resource("dynamodb", endpoint_url=endpoint_url, region_name=region)
    else:
        # AWS DynamoDB
        return boto3.resource("dynamodb", region_name=region)


def initialize_dependencies() -> None:
    """Initialize global dependencies (repositories and validators)."""
    global menu_item_repository, category_repository, api_key_validator

    # Initialize DynamoDB resources
    dynamodb = get_dynamodb_resource()
    menu_items_table_name = os.getenv("MENU_ITEMS_TABLE", "menu_items")
    categories_table_name = os.getenv("CATEGORIES_TABLE", "categories")

    menu_items_table = dynamodb.Table(menu_items_table_name)  # type: ignore[attr-defined]
    categories_table = dynamodb.Table(categories_table_name)  # type: ignore[attr-defined]

    # Initialize repositories
    menu_item_repository = MenuItemRepository(table=menu_items_table)
    category_repository = CategoryRepository(table=categories_table)

    # Initialize API key validator
    api_keys_str = os.getenv("API_KEYS", "dev-key-123,test-key-456")
    valid_keys = {key.strip() for key in api_keys_str.split(",") if key.strip()}

    # Parse API key permissions from environment (optional)
    # Format: KEY1:rest_001,rest_002;KEY2:rest_003;ADMIN_KEY:*
    key_permissions: dict[str, list[str]] | None = None
    permissions_str = os.getenv("API_KEY_PERMISSIONS")
    if permissions_str:
        key_permissions = {}
        for mapping in permissions_str.split(";"):
            mapping = mapping.strip()
            if ":" in mapping:
                key, restaurants = mapping.split(":", 1)
                key = key.strip()
                restaurant_list = [r.strip() for r in restaurants.split(",") if r.strip()]
                if key and restaurant_list:
                    key_permissions[key] = restaurant_list

    api_key_validator = APIKeyValidator(valid_keys=valid_keys, key_permissions=key_permissions)


# Create the FastAPI application
app = FastAPI(
    title="Restaurant Menu Service",
    description="Microservice for managing restaurant menus, items, and categories",
    version="0.1.0",
)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize dependencies on application startup."""
    initialize_dependencies()


# Dependency for API key validation
async def verify_api_key(x_api_key: Annotated[str | None, Header()] = None) -> str:
    """Verify API key from X-API-Key header.

    Args:
        x_api_key: API key from request header

    Returns:
        The validated API key

    Raises:
        HTTPException: 401 if API key is missing or invalid
    """
    if not api_key_validator.is_valid(x_api_key):
        raise HTTPException(status_code=401, detail="Missing or invalid API key")
    return x_api_key  # type: ignore[return-value]


# Dependency for restaurant authorization
def verify_restaurant_access(
    restaurant_id: str, api_key: Annotated[str, Depends(verify_api_key)]
) -> None:
    """Verify API key has access to the restaurant.

    Args:
        restaurant_id: The restaurant identifier from URL path
        api_key: The validated API key from verify_api_key dependency

    Raises:
        HTTPException: 403 if API key doesn't have access to restaurant
    """
    if not api_key_validator.can_access_restaurant(api_key, restaurant_id):
        raise HTTPException(
            status_code=403,
            detail=f"API key is not authorized to access restaurant {restaurant_id}",
        )


# ============================================================================
# Health Check Endpoint
# ============================================================================


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Status information
    """
    return {"status": "ok", "service": "menu-service", "version": "0.1.0"}


# ============================================================================
# Menu Items Endpoints
# ============================================================================


@app.get(
    "/menus/{restaurant_id}/items",
    response_model=list[MenuItem],
    dependencies=[Depends(verify_restaurant_access)],
)
@traced("get_items")
async def get_items(restaurant_id: str) -> list[MenuItem]:
    """Get all menu items for a restaurant.

    Args:
        restaurant_id: The restaurant identifier

    Returns:
        List of menu items (empty list if none found)
    """
    return menu_item_repository.list_by_restaurant(restaurant_id)


@app.get(
    "/menus/{restaurant_id}/items/{item_id}",
    response_model=MenuItem,
    dependencies=[Depends(verify_restaurant_access)],
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
    item = menu_item_repository.get(restaurant_id, item_id)
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
    dependencies=[Depends(verify_restaurant_access)],
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

    return menu_item_repository.create(item)


@app.put(
    "/menus/{restaurant_id}/items/{item_id}",
    response_model=MenuItem,
    dependencies=[Depends(verify_restaurant_access)],
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

    updated_item = menu_item_repository.update(item)
    if updated_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found for restaurant {restaurant_id}",
        )
    return updated_item


@app.delete(
    "/menus/{restaurant_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_restaurant_access)],
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
    deleted = menu_item_repository.delete(restaurant_id, item_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found for restaurant {restaurant_id}",
        )


# ============================================================================
# Categories Endpoints
# ============================================================================


@app.get(
    "/menus/{restaurant_id}/categories",
    response_model=list[Category],
    dependencies=[Depends(verify_restaurant_access)],
)
@traced("get_categories")
async def get_categories(restaurant_id: str) -> list[Category]:
    """Get all categories for a restaurant.

    Args:
        restaurant_id: The restaurant identifier

    Returns:
        List of categories sorted by display_order (empty list if none found)
    """
    return category_repository.list_by_restaurant(restaurant_id)


@app.post(
    "/menus/{restaurant_id}/categories",
    response_model=Category,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_restaurant_access)],
)
@traced("create_category")
async def create_category(restaurant_id: str, category: Category) -> Category:
    """Create a new category for a restaurant.

    Args:
        restaurant_id: The restaurant identifier from URL path
        category: The category to create

    Returns:
        The created category

    Raises:
        HTTPException: 400 if restaurant_id in body doesn't match path
    """
    # Validate restaurant_id in body matches path parameter
    if category.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"restaurant_id in body ({category.restaurant_id}) does not match path parameter ({restaurant_id})",
        )

    return category_repository.create(category)


if __name__ == "__main__":
    import uvicorn  # type: ignore[import-not-found]

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
