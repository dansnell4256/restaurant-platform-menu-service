"""API Key validation for securing endpoints.

This module provides simple API key authentication for FastAPI endpoints.
API keys are validated against a configured set of valid keys.
"""


class APIKeyValidator:
    """Validates API keys against a set of valid keys.

    This validator provides simple API key authentication by checking
    if a provided key exists in a set of valid keys.

    Attributes:
        valid_keys: Set of valid API keys for authentication
    """

    def __init__(self, valid_keys: set[str]) -> None:
        """Initialize the validator with a set of valid API keys.

        Args:
            valid_keys: Set of valid API keys to accept
        """
        self.valid_keys = valid_keys

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
