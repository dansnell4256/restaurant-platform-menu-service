"""OpenTelemetry tracing decorators and utilities.

This module provides decorators for adding tracing to functions without
cluttering the business logic. Decorators automatically extract relevant
attributes and create spans with minimal code overhead.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from opentelemetry import trace

# Type variable for preserving function signatures
F = TypeVar("F", bound=Callable[..., Any])


def traced(operation_name: str, service_name: str = "menu-svc") -> Callable[[F], F]:
    """Decorator to add OpenTelemetry tracing to a repository method.

    Automatically extracts restaurant_id and item_id from method arguments
    and adds them as span attributes along with the service name.

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
    """

    def decorator(func: F) -> F:
        tracer = trace.get_tracer(__name__)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.start_as_current_span(operation_name) as span:
                # Always add service name
                span.set_attribute("service.name", service_name)

                # Extract attributes from arguments
                # args[0] is 'self' for instance methods
                if len(args) > 1:
                    first_arg = args[1]

                    # Check if it's an object with restaurant_id and item_id (like MenuItem)
                    if hasattr(first_arg, "restaurant_id"):
                        span.set_attribute("restaurant_id", first_arg.restaurant_id)
                    if hasattr(first_arg, "item_id"):
                        span.set_attribute("item_id", first_arg.item_id)

                    # Otherwise check if first arg is restaurant_id string
                    if isinstance(first_arg, str):
                        span.set_attribute("restaurant_id", first_arg)
                        # item_id might be second arg
                        if len(args) > 2 and isinstance(args[2], str):
                            span.set_attribute("item_id", args[2])

                # Check kwargs for restaurant_id and item_id
                if "restaurant_id" in kwargs:
                    span.set_attribute("restaurant_id", kwargs["restaurant_id"])
                if "item_id" in kwargs:
                    span.set_attribute("item_id", kwargs["item_id"])

                # Execute the actual function
                return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
