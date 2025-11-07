# Architectural Decision Records

This document captures key architectural and design decisions made during the development of the restaurant platform menu service.

## Format

Each decision includes:
- **Date**: When the decision was made
- **Status**: Accepted, Deprecated, Superseded
- **Context**: What problem we're solving
- **Decision**: What we decided to do
- **Consequences**: Trade-offs and implications

---

## ADR-001: Use pyproject.toml instead of requirements.txt

**Date**: 2025-11-06
**Status**: Accepted

**Context**: Need to manage Python dependencies for the project. Two common approaches exist: requirements.txt (traditional) and pyproject.toml (modern PEP 621 standard).

**Decision**: Use pyproject.toml for dependency management with setuptools as the build backend.

**Consequences**:
- **Pros**:
  - Modern Python standard (PEP 621)
  - Single source of truth for project metadata
  - Supports optional dependencies (e.g., `[dev]` extras)
  - Better tooling integration
- **Cons**:
  - Requires Python 3.11+ and setuptools 68+
  - Team must understand pyproject.toml format

---

## ADR-002: Test categorization - Unit/Component/Integration/E2E

**Date**: 2025-11-06
**Status**: Accepted

**Context**: Need clear test categorization. Initially called mocked DynamoDB tests "integration tests," which was inaccurate. Integration tests should test real service integration, not mocked dependencies.

**Decision**: Use four-tier test structure:
1. **Unit**: Pure logic, no dependencies (e.g., MenuItem validation)
2. **Component**: Complete components with mocked dependencies (e.g., Repository + moto)
3. **Integration**: Real AWS services or multiple services together
4. **E2E**: Full user journeys through the system

**Consequences**:
- **Pros**:
  - Accurate terminology aligned with industry standards
  - Clear boundaries for each test type
  - Easy to run subsets of tests (`pytest -m component`)
  - Fast feedback loop (unit → component → integration → e2e)
- **Cons**:
  - Requires discipline to categorize correctly
  - More markers to remember

**Example**:
- Repository tests with moto: `@pytest.mark.component` ✅
- Not "integration" because DynamoDB is mocked ❌

---

## ADR-003: API Key authentication for service-to-service communication

**Date**: 2025-11-06
**Status**: Accepted

**Context**: Need to secure API endpoints. Options included: API keys, JWT tokens, OAuth2, or API Gateway with Lambda authorizers.

**Decision**: Implement simple API key authentication via `X-API-Key` header using FastAPI dependency injection.

**Consequences**:
- **Pros**:
  - Simple to implement and understand
  - Good for service-to-service communication
  - FastAPI dependency injection makes it clean
  - Easy to test with mocked validators
- **Cons**:
  - Less sophisticated than JWT/OAuth2
  - No user context/claims
  - Key rotation requires coordination
- **Future**: Can upgrade to API Gateway + JWT for production with minimal code changes

**Implementation Pattern**:
```python
@app.get("/endpoint", dependencies=[Depends(verify_api_key)])
async def endpoint(...):
    # Business logic
```

---

## ADR-004: Decorator pattern for OpenTelemetry tracing

**Date**: 2025-11-06
**Status**: Accepted

**Context**: Need to add OpenTelemetry tracing to functions without cluttering business logic. Initial approach using context managers doubled function size.

**Decision**: Use decorator pattern (`@traced`) for non-intrusive tracing that works with both sync and async functions.

**Consequences**:
- **Pros**:
  - Single line of code per function (`@traced("operation_name")`)
  - Doesn't clutter business logic
  - Automatically extracts common attributes (restaurant_id, item_id)
  - Works with both sync and async functions
  - Consistent pattern across all layers (repository, service, API)
- **Cons**:
  - Slightly more complex decorator implementation
  - Uses `inspect.iscoroutinefunction()` to detect async

**Implementation Pattern**:
```python
@traced("operation_name")
def sync_function(restaurant_id: str) -> Result:
    return result

@traced("operation_name")
async def async_function(restaurant_id: str) -> Result:
    return result
```

**Key Design**: Decorator automatically detects sync vs async and uses appropriate wrapper.

---

## ADR-005: Consolidated tracing tests across layers

**Date**: 2025-11-06
**Status**: Accepted

**Context**: When adding tracing to API layer, could either create separate tracing test file for each layer or consolidate into one file demonstrating the pattern works everywhere.

**Decision**: Consolidate tracing tests into single `test_tracing.py` file with examples from each layer (repository and API).

**Consequences**:
- **Pros**:
  - Avoids redundant test duplication
  - Single file shows tracing works consistently
  - DRY principle - we test the decorator mechanism once
  - Demonstrates pattern with representative examples
  - Easier to maintain
- **Cons**:
  - File mixes different layer concerns
  - Slightly longer test file

**Rationale**: The `@traced` decorator mechanism is proven to work at the repository layer (5 tests). We only need 1-2 examples at the API layer to demonstrate it works there too. We don't need exhaustive testing for every endpoint since the decorator pattern is consistent.

**Test Structure**:
```
test_tracing.py
├── Repository layer tests (5 examples - sync functions)
│   ├── create, get, list, update, delete
└── API layer tests (1 example - async function)
    └── get_items endpoint
```

---

## ADR-006: Async support in tracing decorator

**Date**: 2025-11-06
**Status**: Accepted

**Context**: FastAPI endpoints are async functions. Initial `@traced` decorator only supported sync functions, causing coroutine errors when applied to async endpoints.

**Decision**: Enhanced `@traced` decorator to detect function type and use appropriate wrapper (sync or async).

**Consequences**:
- **Pros**:
  - Single decorator works everywhere
  - No separate `@traced_async` decorator needed
  - Automatic detection via `inspect.iscoroutinefunction()`
  - Developer doesn't need to think about it
- **Cons**:
  - Slightly more complex implementation
  - Two code paths to maintain (but DRY with helper function)

**Implementation Details**:
- Extract span attribute logic into `_extract_span_attributes()` helper
- Both sync and async wrappers call same helper
- Async wrapper properly awaits the decorated function

---

## Future Decisions to Document

As development continues, document decisions about:
- Service layer patterns (if implemented)
- Event publishing strategies (EventBridge)
- Error handling patterns
- Input validation strategies
- Caching approaches
- Rate limiting implementation
- AWS infrastructure choices (CDK patterns)
