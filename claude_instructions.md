# Claude Code Development Instructions

## Project: Restaurant Platform Menu Service

### Development Philosophy
1. **Test-Driven Development (TDD)**: Always write tests FIRST to explain what the system is doing
2. **Incremental Development**: Build very small, focused pieces at a time
3. **Observability First**: Bake in OpenTelemetry from the start - every function should have tracing
4. **Trunk-Based Development**: Short-lived feature branches (1-2 days max), commit to main frequently
5. **Explain as We Go**: Document what each function and class does and its purpose

### Technology Stack & Architecture
- **Language**: Python 3.11+
- **Testing**: pytest as test harness with >80% coverage
- **Cloud**: AWS Serverless Architecture
  - **API**: API Gateway REST endpoints
  - **Compute**: Lambda functions
  - **Storage**: DynamoDB (menu items, categories, pricing)
  - **Events**: EventBridge for menu change notifications
  - **Caching**: ElastiCache for frequently accessed data
- **Monitoring**: OpenTelemetry + AWS X-Ray + CloudWatch
- **CI/CD**: GitHub Actions with trunk-based workflow

### Repository Convention
- **Name**: `restaurant-platform-menu-service`
- **Service ID**: `menu-svc` (for logging/tracing)
- **Branch Strategy**:
  - `main` - single source of truth, always deployable
  - `feature/{ticket-id}-{brief-description}` - short-lived only
  - No long-running branches (no develop, staging branches)

### Development Workflow
1. **Write Test First**: Explain the behavior you want
2. **Implement Minimum**: Just enough code to make test pass
3. **Add Observability**: Include OpenTelemetry spans and metrics
4. **Refactor**: Clean up while keeping tests green
5. **Commit Small**: Frequent commits with conventional commit messages

### Service Responsibilities
This menu service is responsible for:
- **Menu Item Management**: CRUD operations for dishes, descriptions, ingredients
- **Category Management**: Organization and hierarchy of menu sections
- **Pricing Rules**: Base prices, modifiers, time-based pricing
- **Availability Scheduling**: When items are available (hours, days, seasonal)
- **Event Publishing**: Notify downstream services of menu changes via EventBridge
- **Admin API**: REST endpoints for restaurant admin frontend

### Key Data Models (DynamoDB Design)
- **Menu Items Table**:
  - Partition Key: `restaurant_id`
  - Sort Key: `item_id`
  - Attributes: name, description, price, category, availability, allergens
- **Categories Table**:
  - Partition Key: `restaurant_id`
  - Sort Key: `category_id`
  - Attributes: name, display_order, parent_category

### API Endpoints to Build
```
GET    /menus/{restaurant_id}/items           # List all menu items
POST   /menus/{restaurant_id}/items           # Create new menu item
GET    /menus/{restaurant_id}/items/{item_id} # Get specific item
PUT    /menus/{restaurant_id}/items/{item_id} # Update menu item
DELETE /menus/{restaurant_id}/items/{item_id} # Delete menu item
GET    /menus/{restaurant_id}/categories      # List categories
POST   /menus/{restaurant_id}/categories      # Create category
GET    /health                                # Health check endpoint
```

### Integration with Platform
- **Publishes Events**: Menu item changes → EventBridge → Aggregation Service
- **Consumed By**:
  - `restaurant-platform-aggregation-service` (menu formatting)
  - `restaurant-platform-admin-web` (restaurant management UI)
  - External platform adapters (DoorDash, GrubHub)

### Quality Standards & Gates
- **Test Coverage**: Minimum 80% coverage with pytest
- **Code Quality**: Black formatting, Ruff linting, MyPy type checking
- **Security**: Dependency vulnerability scanning
- **Performance**: OpenTelemetry metrics for response times
- **Branch Protection**: Require PR approval + all checks passing

### Deployment Strategy
- **DEV Environment**: Auto-deploy on every commit to main
- **STAGING Environment**: Auto-deploy after successful DEV deployment
- **PROD Environment**: Manual approval required via GitHub Environments
- **Rollback Strategy**: Blue/green deployments with CloudWatch alarms

### Observability Requirements
- **Service Identification**: All logs/traces tagged with `service=menu-svc`
- **Custom Metrics**:
  - Menu item creation/update/delete rates
  - API response times by endpoint
  - Error rates by operation type
- **Tracing**: Every Lambda function and DynamoDB operation traced
- **Alerting**: CloudWatch alarms for error rates, latency, availability

### Development Priorities (Build Order)
1. **Core Data Models**: MenuItem, Category classes with validation
2. **DynamoDB Repository**: Basic CRUD operations with mocking for tests
3. **Business Logic**: Menu item creation, updates, validation rules
4. **API Layer**: FastAPI endpoints with proper error handling
5. **Event Publishing**: EventBridge integration for menu changes
6. **Infrastructure**: CDK for AWS resources (Lambda, API Gateway, DynamoDB)
7. **CI/CD Pipeline**: GitHub Actions for testing and deployment

### File Structure
```
src/
├── models/          # Pydantic models for MenuItem, Category
├── repositories/    # DynamoDB data access layer
├── services/        # Business logic layer
├── api/            # FastAPI route handlers
├── events/         # EventBridge publishing
├── security/        # Authentication/authorization utilities
├── observability/   # OpenTelemetry tracing decorators
└── infrastructure/ # CDK infrastructure code

tests/
├── unit/           # Pure logic, no dependencies (MenuItem validation)
├── component/      # Complete components with mocked deps (Repository + moto)
├── integration/    # Real AWS services or multiple services together
└── e2e/            # Full user journeys through the entire system
```

### Getting Started Checklist
- [x] Set up Python project structure with pyproject.toml
- [x] Configure pytest with coverage and testing markers
- [x] Set up pre-commit hooks for code quality
- [x] Create basic MenuItem model with tests (TDD)
- [x] Implement DynamoDB repository pattern with moto mocking
- [x] Add OpenTelemetry instrumentation from first function
- [x] Create GitHub Actions CI pipeline

### Implementation Patterns

#### OpenTelemetry Tracing Pattern
Use the `@traced` decorator for non-intrusive observability. It works with both sync and async functions.

```python
from src.observability.tracing import traced

# Sync function (repository layer)
@traced("operation_name")
def create(self, item: MenuItem) -> MenuItem:
    return item

# Async function (API layer)
@traced("operation_name")
async def get_items(restaurant_id: str) -> list[MenuItem]:
    return items
```

**Tracing Guidelines**:
- Add `@traced` to ALL functions in repository, service, and API layers
- Decorator automatically extracts `restaurant_id` and `item_id` from arguments
- Use descriptive operation names (e.g., "create", "get", "list_by_restaurant")
- Don't manually create spans - let the decorator handle it
- Test tracing with examples from each layer (see `tests/component/test_tracing.py`)

#### API Security Pattern
Use FastAPI dependency injection for API key validation:

```python
from src.security.api_key_validator import APIKeyValidator

# In create_app function
async def verify_api_key(x_api_key: str | None = Header()) -> None:
    if not api_key_validator.is_valid(x_api_key):
        raise HTTPException(status_code=401, detail="Missing or invalid API key")

@app.get("/endpoint", dependencies=[Depends(verify_api_key)])
async def endpoint(...):
    # Business logic
```

**Security Guidelines**:
- ALL API endpoints must have `dependencies=[Depends(verify_api_key)]`
- API keys passed via `X-API-Key` header
- Validator injected via dependency injection for easy testing
- Test with mocked validators (see `tests/component/test_api_menu_items.py`)

#### Testing Strategy
**Don't duplicate tests unnecessarily**. Test the mechanism once, then trust the pattern.

**Example**: For OpenTelemetry tracing
- ✅ Test decorator works at repository layer (5 examples in `test_tracing.py`)
- ✅ Test decorator works at API layer (1 example in `test_tracing.py`)
- ❌ DON'T test tracing for every single endpoint - the decorator is proven

**Test File Organization**:
- Consolidate related cross-cutting concerns (e.g., all tracing tests in one file)
- Group by feature/component for functional tests (e.g., `test_api_menu_items.py`)
- Avoid redundant test files that test the same decorator/pattern repeatedly

**Dependency Management Note**: This project uses `pyproject.toml` (PEP 621) for dependency management - the modern Python standard. No `requirements.txt` files are needed. Install dependencies using `pip install -e ".[dev]"` within a virtual environment.

**Architectural Decisions**: All major design decisions are documented in `DECISIONS.md` using the ADR (Architectural Decision Record) format. When making significant choices, add a new ADR with context, decision, and consequences.

**Remember**: Start with the smallest possible piece (like a MenuItem model) and build incrementally. Write the test first to explain what you're building, then implement just enough to make it pass.
