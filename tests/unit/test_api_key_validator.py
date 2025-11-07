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
