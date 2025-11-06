"""Component tests for MenuItemRepository OpenTelemetry tracing.

This test verifies that repository operations are decorated with OpenTelemetry tracing:
- Each CRUD operation creates a span with @traced decorator
- Spans include service name and operation identifiers as attributes
- Tracing is non-intrusive and doesn't clutter business logic
"""

from collections.abc import Generator
from decimal import Decimal
from typing import Any

import boto3
import pytest
from moto import mock_aws
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from src.models.menu_item import MenuItem
from src.repositories.menu_item_repository import MenuItemRepository


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
