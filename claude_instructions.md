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

### File Structure to Create
```
src/
├── models/          # Pydantic models for MenuItem, Category
├── repositories/    # DynamoDB data access layer
├── services/        # Business logic layer
├── api/            # FastAPI route handlers
├── events/         # EventBridge publishing
└── infrastructure/ # CDK infrastructure code

tests/
├── unit/           # Fast isolated tests
├── integration/    # Tests with real AWS services (mocked)
└── e2e/           # End-to-end API tests
```

### Getting Started Checklist
- [ ] Set up Python project structure with pyproject.toml
- [ ] Configure pytest with coverage and testing markers
- [ ] Set up pre-commit hooks for code quality
- [ ] Create basic MenuItem model with tests (TDD)
- [ ] Implement DynamoDB repository pattern with moto mocking
- [ ] Add OpenTelemetry instrumentation from first function
- [ ] Create GitHub Actions CI pipeline

**Remember**: Start with the smallest possible piece (like a MenuItem model) and build incrementally. Write the test first to explain what you're building, then implement just enough to make it pass.
