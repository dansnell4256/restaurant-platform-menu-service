"""Unit tests for main application entry point."""

import os
from unittest.mock import patch

import pytest

from src.main import get_dynamodb_resource


@pytest.mark.unit
def test_get_dynamodb_resource_sets_credentials_for_local_endpoint() -> None:
    """Test that get_dynamodb_resource sets dummy credentials for local endpoints."""
    # Clear any existing credentials
    env_backup = {
        "AWS_ACCESS_KEY_ID": os.environ.pop("AWS_ACCESS_KEY_ID", None),
        "AWS_SECRET_ACCESS_KEY": os.environ.pop("AWS_SECRET_ACCESS_KEY", None),
    }

    try:
        with (
            patch.dict(os.environ, {"DYNAMODB_ENDPOINT": "http://localhost:8000"}),
            patch("src.main.boto3.resource") as mock_resource,
        ):
            get_dynamodb_resource()

            # Verify dummy credentials were set
            assert os.environ["AWS_ACCESS_KEY_ID"] == "testing"
            assert os.environ["AWS_SECRET_ACCESS_KEY"] == "testing"

            # Verify boto3.resource was called with endpoint
            mock_resource.assert_called_once_with(
                "dynamodb", endpoint_url="http://localhost:8000", region_name="us-east-1"
            )
    finally:
        # Restore original environment
        if env_backup["AWS_ACCESS_KEY_ID"]:
            os.environ["AWS_ACCESS_KEY_ID"] = env_backup["AWS_ACCESS_KEY_ID"]
        elif "AWS_ACCESS_KEY_ID" in os.environ:
            del os.environ["AWS_ACCESS_KEY_ID"]

        if env_backup["AWS_SECRET_ACCESS_KEY"]:
            os.environ["AWS_SECRET_ACCESS_KEY"] = env_backup["AWS_SECRET_ACCESS_KEY"]
        elif "AWS_SECRET_ACCESS_KEY" in os.environ:
            del os.environ["AWS_SECRET_ACCESS_KEY"]


@pytest.mark.unit
def test_get_dynamodb_resource_preserves_existing_credentials() -> None:
    """Test that get_dynamodb_resource doesn't override existing credentials."""
    with (
        patch.dict(
            os.environ,
            {
                "DYNAMODB_ENDPOINT": "http://localhost:8000",
                "AWS_ACCESS_KEY_ID": "existing-key",
                "AWS_SECRET_ACCESS_KEY": "existing-secret",
            },
        ),
        patch("src.main.boto3.resource") as mock_resource,
    ):
        get_dynamodb_resource()

        # Verify existing credentials were preserved
        assert os.environ["AWS_ACCESS_KEY_ID"] == "existing-key"
        assert os.environ["AWS_SECRET_ACCESS_KEY"] == "existing-secret"

        mock_resource.assert_called_once_with(
            "dynamodb", endpoint_url="http://localhost:8000", region_name="us-east-1"
        )


@pytest.mark.unit
def test_get_dynamodb_resource_uses_aws_without_endpoint() -> None:
    """Test that get_dynamodb_resource uses AWS DynamoDB when no endpoint is set."""
    with (
        patch.dict(os.environ, {"DYNAMODB_ENDPOINT": ""}, clear=False),
        patch("src.main.boto3.resource") as mock_resource,
    ):
        # Remove DYNAMODB_ENDPOINT if it exists
        if "DYNAMODB_ENDPOINT" in os.environ:
            del os.environ["DYNAMODB_ENDPOINT"]

        get_dynamodb_resource()

        # Verify boto3.resource was called without endpoint
        mock_resource.assert_called_once_with("dynamodb", region_name="us-east-1")


@pytest.mark.unit
def test_get_dynamodb_resource_uses_custom_region() -> None:
    """Test that get_dynamodb_resource respects AWS_REGION environment variable."""
    with (
        patch.dict(
            os.environ,
            {"DYNAMODB_ENDPOINT": "http://localhost:8000", "AWS_REGION": "eu-west-1"},
        ),
        patch("src.main.boto3.resource") as mock_resource,
    ):
        get_dynamodb_resource()

        mock_resource.assert_called_once_with(
            "dynamodb", endpoint_url="http://localhost:8000", region_name="eu-west-1"
        )
