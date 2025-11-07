"""OpenTelemetry tracing decorators and utilities.

This module provides decorators for adding tracing to functions without
cluttering the business logic. Decorators automatically extract relevant
attributes and create spans with minimal code overhead.

Supports both synchronous and asynchronous functions.
"""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from opentelemetry import trace

# Type variable for preserving function signatures
F = TypeVar("F", bound=Callable[..., Any])


def traced(operation_name: str, service_name: str = "menu-svc") -> Callable[[F], F]:
    """Decorator to add OpenTelemetry tracing to sync or async functions.

    Automatically extracts restaurant_id and item_id from method arguments
    and adds them as span attributes along with the service name.

    Works with both synchronous and asynchronous functions.

    Args:
        operation_name: Name of the operation (e.g., "create", "get", "update")
        service_name: Service identifier for tracing (default: "menu-svc")

    Returns:
        Decorated function with automatic tracing

    Example:
        @traced("create")
        def create(self, item: MenuItem) -> MenuItem:
            # Business logic here
            return item

        @traced("get_items")
        async def get_items(restaurant_id: str) -> list[MenuItem]:
            # Async business logic here
            return items
    """

    def decorator(func: F) -> F:
        tracer = trace.get_tracer(__name__)

        # Check if the function is async
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with tracer.start_as_current_span(operation_name) as span:
                    # Always add service name
                    span.set_attribute("service.name", service_name)

                    # Extract attributes from arguments
                    _extract_span_attributes(span, args, kwargs)

                    # Execute the actual async function
                    return await func(*args, **kwargs)

            return async_wrapper  # type: ignore[return-value]

        else:

            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                with tracer.start_as_current_span(operation_name) as span:
                    # Always add service name
                    span.set_attribute("service.name", service_name)

                    # Extract attributes from arguments
                    _extract_span_attributes(span, args, kwargs)

                    # Execute the actual function
                    return func(*args, **kwargs)

            return sync_wrapper  # type: ignore[return-value]

    return decorator


def _extract_span_attributes(span: Any, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
    """Extract restaurant_id and item_id from function arguments and add to span.

    Args:
        span: OpenTelemetry span to add attributes to
        args: Positional arguments from the function call
        kwargs: Keyword arguments from the function call
    """
    # args[0] might be 'self' for instance methods, or first param for functions
    # Check first non-self argument
    arg_start = 1 if len(args) > 1 else 0

    if len(args) > arg_start:
        first_arg = args[arg_start]

        # Check if it's an object with restaurant_id and item_id (like MenuItem)
        if hasattr(first_arg, "restaurant_id"):
            span.set_attribute("restaurant_id", first_arg.restaurant_id)
        if hasattr(first_arg, "item_id"):
            span.set_attribute("item_id", first_arg.item_id)

        # Otherwise check if first arg is restaurant_id string
        if isinstance(first_arg, str):
            span.set_attribute("restaurant_id", first_arg)
            # item_id might be second arg
            if len(args) > arg_start + 1 and isinstance(args[arg_start + 1], str):
                span.set_attribute("item_id", args[arg_start + 1])

    # Check kwargs for restaurant_id and item_id
    if "restaurant_id" in kwargs:
        span.set_attribute("restaurant_id", kwargs["restaurant_id"])
    if "item_id" in kwargs:
        span.set_attribute("item_id", kwargs["item_id"])
