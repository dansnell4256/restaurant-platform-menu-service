"""API Key validation for securing endpoints.

This module provides simple API key authentication for FastAPI endpoints.
API keys are validated against a configured set of valid keys, and can
optionally be mapped to specific restaurant permissions.
"""


class APIKeyValidator:
    """Validates API keys and checks restaurant access permissions.

    This validator provides API key authentication and authorization by:
    1. Checking if a provided key exists in a set of valid keys
    2. Validating that the key has access to specific restaurants

    Attributes:
        valid_keys: Set of valid API keys for authentication
        key_permissions: Mapping of API keys to restaurant IDs they can access
                        Use "*" as a restaurant ID to grant access to all restaurants
    """

    def __init__(
        self,
        valid_keys: set[str],
        key_permissions: dict[str, list[str]] | None = None,
    ) -> None:
        """Initialize the validator with API keys and their permissions.

        Args:
            valid_keys: Set of valid API keys to accept
            key_permissions: Optional mapping of API keys to restaurant IDs.
                           If None, all valid keys have access to all restaurants (legacy mode).
                           Use ["*"] as the restaurant list to grant access to all restaurants.

        Example:
            validator = APIKeyValidator(
                valid_keys={"key1", "key2", "admin_key"},
                key_permissions={
                    "key1": ["rest_123", "rest_456"],
                    "key2": ["rest_789"],
                    "admin_key": ["*"]  # Access to all restaurants
                }
            )
        """
        self.valid_keys = valid_keys
        self.key_permissions = key_permissions or {}

    def is_valid(self, api_key: str | None) -> bool:
        """Check if the provided API key is valid.

        Args:
            api_key: The API key to validate

        Returns:
            True if the key is valid, False otherwise
        """
        if not api_key:
            return False

        return api_key in self.valid_keys

    def can_access_restaurant(self, api_key: str | None, restaurant_id: str) -> bool:
        """Check if the API key has access to a specific restaurant.

        Args:
            api_key: The API key to check
            restaurant_id: The restaurant ID to check access for

        Returns:
            True if the key can access the restaurant, False otherwise
        """
        if not api_key or not self.is_valid(api_key):
            return False

        # If no permissions configured, allow all (legacy mode)
        if not self.key_permissions:
            return True

        # If key not in permissions, deny access
        if api_key not in self.key_permissions:
            return False

        allowed_restaurants = self.key_permissions[api_key]

        # Check for wildcard access
        if "*" in allowed_restaurants:
            return True

        # Check if specific restaurant is allowed
        return restaurant_id in allowed_restaurants
