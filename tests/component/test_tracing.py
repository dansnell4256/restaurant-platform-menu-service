"""Component tests for OpenTelemetry tracing across application layers.

This test verifies that the @traced decorator works consistently across layers:
- Repository operations create spans with appropriate attributes
- API endpoints create spans with HTTP context
- Spans include service name and operation identifiers
- Tracing is non-intrusive and doesn't clutter business logic

Note: We test examples from each layer to demonstrate the decorator pattern works
consistently. We don't exhaustively test every endpoint since the decorator itself
is proven to work.
"""

from collections.abc import Generator
from decimal import Decimal
from typing import Any
from unittest.mock import Mock

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from src.api.menu_items import create_app
from src.models.menu_item import MenuItem
from src.repositories.menu_item_repository import MenuItemRepository
from src.security.api_key_validator import APIKeyValidator


@pytest.fixture(scope="session")
def tracer_provider() -> TracerProvider:
    """Set up OpenTelemetry tracer provider with in-memory exporter (session-scoped)."""
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    return provider


@pytest.fixture
def dynamodb_table() -> Generator[Any, None, None]:
    """Create a mocked DynamoDB table for testing."""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="menu-items",
            KeySchema=[
                {"AttributeName": "restaurant_id", "KeyType": "HASH"},
                {"AttributeName": "item_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "restaurant_id", "AttributeType": "S"},
                {"AttributeName": "item_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield table


@pytest.fixture
def repository(dynamodb_table: Any) -> MenuItemRepository:
    """Create MenuItemRepository with mocked DynamoDB table."""
    return MenuItemRepository(table=dynamodb_table)


@pytest.mark.component
def test_create_operation_creates_span(
    repository: MenuItemRepository,
    tracer_provider: TracerProvider,
) -> None:
    """Test that create operation creates a tracing span with decorator."""
    # Set up span exporter for this test
    span_exporter = InMemorySpanExporter()
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))

    item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_456",
        name="Margherita Pizza",
        price=Decimal("12.99"),
    )

    repository.create(item)

    spans = span_exporter.get_finished_spans()
    assert len(spans) > 0

    # Find span by name
    create_span = next((s for s in spans if "create" in s.name), None)
    assert create_span is not None
    assert create_span.attributes["service.name"] == "menu-svc"
    assert create_span.attributes["restaurant_id"] == "rest_123"
    assert create_span.attributes["item_id"] == "item_456"


@pytest.mark.component
def test_get_operation_creates_span(
    repository: MenuItemRepository,
    tracer_provider: TracerProvider,
) -> None:
    """Test that get operation creates a tracing span."""
    # Set up span exporter for this test
    span_exporter = InMemorySpanExporter()
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))

    item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_456",
        name="Margherita Pizza",
        price=Decimal("12.99"),
    )
    repository.create(item)
    span_exporter.clear()

    repository.get("rest_123", "item_456")

    spans = span_exporter.get_finished_spans()
    get_span = next((s for s in spans if "get" in s.name), None)
    assert get_span is not None
    assert get_span.attributes["service.name"] == "menu-svc"
    assert get_span.attributes["restaurant_id"] == "rest_123"
    assert get_span.attributes["item_id"] == "item_456"


@pytest.mark.component
def test_list_operation_creates_span(
    repository: MenuItemRepository,
    tracer_provider: TracerProvider,
) -> None:
    """Test that list_by_restaurant operation creates a tracing span."""
    # Set up span exporter for this test
    span_exporter = InMemorySpanExporter()
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))

    repository.list_by_restaurant("rest_123")

    spans = span_exporter.get_finished_spans()
    list_span = next((s for s in spans if "list" in s.name), None)
    assert list_span is not None
    assert list_span.attributes["service.name"] == "menu-svc"
    assert list_span.attributes["restaurant_id"] == "rest_123"


@pytest.mark.component
def test_update_operation_creates_span(
    repository: MenuItemRepository,
    tracer_provider: TracerProvider,
) -> None:
    """Test that update operation creates a tracing span."""
    # Set up span exporter for this test
    span_exporter = InMemorySpanExporter()
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))

    item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_456",
        name="Margherita Pizza",
        price=Decimal("12.99"),
    )
    repository.create(item)
    span_exporter.clear()

    updated_item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_456",
        name="Margherita Pizza (Large)",
        price=Decimal("15.99"),
    )
    repository.update(updated_item)

    spans = span_exporter.get_finished_spans()
    # Note: update calls get() internally, so filter for update span
    update_span = next((s for s in spans if "update" in s.name), None)
    assert update_span is not None
    assert update_span.attributes["service.name"] == "menu-svc"
    assert update_span.attributes["restaurant_id"] == "rest_123"
    assert update_span.attributes["item_id"] == "item_456"


@pytest.mark.component
def test_delete_operation_creates_span(
    repository: MenuItemRepository,
    tracer_provider: TracerProvider,
) -> None:
    """Test that delete operation creates a tracing span."""
    # Set up span exporter for this test
    span_exporter = InMemorySpanExporter()
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))

    item = MenuItem(
        restaurant_id="rest_123",
        item_id="item_456",
        name="Margherita Pizza",
        price=Decimal("12.99"),
    )
    repository.create(item)
    span_exporter.clear()

    repository.delete("rest_123", "item_456")

    spans = span_exporter.get_finished_spans()
    # Note: delete calls get() internally, so filter for delete span
    delete_span = next((s for s in spans if "delete" in s.name), None)
    assert delete_span is not None
    assert delete_span.attributes["service.name"] == "menu-svc"
    assert delete_span.attributes["restaurant_id"] == "rest_123"
    assert delete_span.attributes["item_id"] == "item_456"


# API Layer Tracing Tests
# These tests demonstrate the @traced decorator works at the API layer too


@pytest.fixture
def mock_repository() -> Mock:
    """Create a mock MenuItemRepository for API testing."""
    return Mock()


@pytest.fixture
def api_key_validator() -> APIKeyValidator:
    """Create API key validator with test keys."""
    return APIKeyValidator(valid_keys={"test-key-123"})


@pytest.fixture
def api_client(
    mock_repository: Mock,
    api_key_validator: APIKeyValidator,
) -> Generator[TestClient, None, None]:
    """Create FastAPI test client with mocked dependencies."""
    app = create_app(repository=mock_repository, api_key_validator=api_key_validator)
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.component
def test_api_get_items_creates_span(
    api_client: TestClient,
    mock_repository: Mock,
    tracer_provider: TracerProvider,
) -> None:
    """Test that API endpoint creates tracing span with decorator.

    This demonstrates the @traced decorator works at the API layer,
    just like it does at the repository layer.
    """
    # Set up span exporter for this test
    span_exporter = InMemorySpanExporter()
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))

    # Arrange
    mock_repository.list_by_restaurant.return_value = []

    # Act
    response = api_client.get(
        "/restaurants/rest_123/items",
        headers={"X-API-Key": "test-key-123"},
    )

    # Assert
    assert response.status_code == 200

    # Verify API span was created
    spans = span_exporter.get_finished_spans()
    api_span = next((s for s in spans if "get_items" in s.name), None)
    assert api_span is not None
    assert api_span.attributes["service.name"] == "menu-svc"
    assert api_span.attributes["restaurant_id"] == "rest_123"
