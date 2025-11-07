"""Unit tests for API key validation.

This test verifies the API key validation logic:
- Valid API keys are accepted
- Invalid API keys are rejected
- Missing API keys are rejected
- Keys are loaded from configuration
"""

import pytest

from src.security.api_key_validator import APIKeyValidator


@pytest.mark.unit
def test_valid_api_key_accepted() -> None:
    """Test that a valid API key is accepted."""
    validator = APIKeyValidator(valid_keys={"test-key-123", "test-key-456"})

    assert validator.is_valid("test-key-123") is True
    assert validator.is_valid("test-key-456") is True


@pytest.mark.unit
def test_invalid_api_key_rejected() -> None:
    """Test that an invalid API key is rejected."""
    validator = APIKeyValidator(valid_keys={"test-key-123"})

    assert validator.is_valid("wrong-key") is False
    assert validator.is_valid("test-key-456") is False


@pytest.mark.unit
def test_empty_api_key_rejected() -> None:
    """Test that an empty API key is rejected."""
    validator = APIKeyValidator(valid_keys={"test-key-123"})

    assert validator.is_valid("") is False


@pytest.mark.unit
def test_none_api_key_rejected() -> None:
    """Test that None API key is rejected."""
    validator = APIKeyValidator(valid_keys={"test-key-123"})

    assert validator.is_valid(None) is False


@pytest.mark.unit
def test_validator_with_no_valid_keys() -> None:
    """Test that validator with no valid keys rejects all keys."""
    validator = APIKeyValidator(valid_keys=set())

    assert validator.is_valid("any-key") is False


@pytest.mark.unit
def test_validator_case_sensitive() -> None:
    """Test that API key validation is case-sensitive."""
    validator = APIKeyValidator(valid_keys={"Test-Key-123"})

    assert validator.is_valid("Test-Key-123") is True
    assert validator.is_valid("test-key-123") is False
    assert validator.is_valid("TEST-KEY-123") is False


# Restaurant Authorization Tests


@pytest.mark.unit
def test_can_access_restaurant_with_permissions() -> None:
    """Test that API key with permissions can access authorized restaurants."""
    validator = APIKeyValidator(
        valid_keys={"key1", "key2"},
        key_permissions={
            "key1": ["rest_123", "rest_456"],
            "key2": ["rest_789"],
        },
    )

    assert validator.can_access_restaurant("key1", "rest_123") is True
    assert validator.can_access_restaurant("key1", "rest_456") is True
    assert validator.can_access_restaurant("key2", "rest_789") is True


@pytest.mark.unit
def test_cannot_access_unauthorized_restaurant() -> None:
    """Test that API key cannot access restaurants it's not authorized for."""
    validator = APIKeyValidator(
        valid_keys={"key1", "key2"},
        key_permissions={
            "key1": ["rest_123"],
            "key2": ["rest_789"],
        },
    )

    assert validator.can_access_restaurant("key1", "rest_789") is False
    assert validator.can_access_restaurant("key2", "rest_123") is False
    assert validator.can_access_restaurant("key1", "rest_999") is False


@pytest.mark.unit
def test_wildcard_access_to_all_restaurants() -> None:
    """Test that API key with wildcard (*) can access any restaurant."""
    validator = APIKeyValidator(
        valid_keys={"admin_key", "regular_key"},
        key_permissions={
            "admin_key": ["*"],
            "regular_key": ["rest_123"],
        },
    )

    assert validator.can_access_restaurant("admin_key", "rest_123") is True
    assert validator.can_access_restaurant("admin_key", "rest_456") is True
    assert validator.can_access_restaurant("admin_key", "rest_any") is True
    assert validator.can_access_restaurant("regular_key", "rest_123") is True
    assert validator.can_access_restaurant("regular_key", "rest_456") is False


@pytest.mark.unit
def test_legacy_mode_no_permissions_allows_all() -> None:
    """Test that when no permissions configured, all valid keys can access all restaurants."""
    validator = APIKeyValidator(valid_keys={"key1", "key2"})

    # Legacy mode - no permissions configured, should allow all
    assert validator.can_access_restaurant("key1", "rest_123") is True
    assert validator.can_access_restaurant("key1", "rest_456") is True
    assert validator.can_access_restaurant("key2", "rest_789") is True


@pytest.mark.unit
def test_invalid_key_cannot_access_restaurant() -> None:
    """Test that invalid API key cannot access any restaurant."""
    validator = APIKeyValidator(
        valid_keys={"key1"},
        key_permissions={"key1": ["rest_123"]},
    )

    assert validator.can_access_restaurant("invalid_key", "rest_123") is False
    assert validator.can_access_restaurant(None, "rest_123") is False
    assert validator.can_access_restaurant("", "rest_123") is False


@pytest.mark.unit
def test_valid_key_not_in_permissions_denied() -> None:
    """Test that valid API key not in permissions map is denied access."""
    validator = APIKeyValidator(
        valid_keys={"key1", "key2"},
        key_permissions={
            "key1": ["rest_123"],
            # key2 is valid but not in permissions
        },
    )

    assert validator.can_access_restaurant("key1", "rest_123") is True
    assert validator.can_access_restaurant("key2", "rest_123") is False
    assert validator.can_access_restaurant("key2", "rest_456") is False


@pytest.mark.unit
def test_empty_permissions_list_denies_all() -> None:
    """Test that API key with empty permissions list cannot access any restaurant."""
    validator = APIKeyValidator(
        valid_keys={"key1"},
        key_permissions={"key1": []},
    )

    assert validator.can_access_restaurant("key1", "rest_123") is False
    assert validator.can_access_restaurant("key1", "rest_456") is False
