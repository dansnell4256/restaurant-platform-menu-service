# Restaurant Platform - Menu Service

## Overview
Microservice responsible for CRUD operations on menu items, categories, pricing, and availability management. This service provides the foundational data layer for the restaurant platform's menu aggregation system.

## Purpose
- Manage restaurant menu items and categories
- Handle pricing rules and availability schedules
- Provide APIs for menu administration
- Publish menu change events for downstream services

## Tech Stack
- **Python 3.11+** - Core language
- **FastAPI** - REST API framework
- **DynamoDB** - Data storage
- **AWS Lambda** - Serverless compute
- **OpenTelemetry** - Observability and tracing
- **pytest** - Testing framework

## Quick Start

### Prerequisites
- Python 3.11 or higher
- Git

### Setup
```bash
# Clone the repository
git clone <repo-url>
cd restaurant-platform-menu-service

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Locally

```bash
# Install uvicorn if not already installed
pip install uvicorn

# Option 1: Run with uvicorn directly (recommended for development)
uvicorn src.main:app --reload --port 8000

# Option 2: Run with Python
python -m src.main

# The API will be available at:
# - API Documentation: http://localhost:8000/api/v1/docs
# - Health Check: http://localhost:8000/api/v1/health
# - Menu Items: http://localhost:8000/api/v1/menus/{restaurant_id}/items
# - Categories: http://localhost:8000/api/v1/menus/{restaurant_id}/categories
```

#### Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key environment variables:
- `API_KEYS` - Comma-separated list of valid API keys (default: `dev-key-123,test-key-456`)
- `DYNAMODB_ENDPOINT` - For local DynamoDB (leave unset for AWS)
- `AWS_REGION` - AWS region (default: `us-east-1`)
- `MENU_ITEMS_TABLE` - DynamoDB table name for menu items
- `CATEGORIES_TABLE` - DynamoDB table name for categories

**Note:** For local development, you need a DynamoDB backend. **We recommend LocalStack** (option 1):

1. **LocalStack (Recommended)** - Full local AWS environment
   ```bash
   docker compose up -d
   ./scripts/init-localstack.sh
   ```
   See [LOCALSTACK.md](LOCALSTACK.md) for complete setup guide.

2. **Local DynamoDB** - Run DynamoDB locally via Docker: `docker run -p 8000:8000 amazon/dynamodb-local`

3. **Real AWS** - Point to actual DynamoDB tables (requires AWS credentials)

4. **Moto** - Used automatically in tests, not ideal for interactive development

### Development Commands

```bash
# Run tests
pytest -v

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run specific test markers
pytest -m unit          # Unit tests only
pytest -m component     # Component tests only
pytest -m integration   # Integration tests only
pytest -m e2e           # E2E tests only

# Run linting and formatting
pre-commit run --all-files              # Run on all files
pre-commit run --files <file>           # Run on specific files

# Format code
black .

# Lint code
ruff check . --fix

# Type checking
mypy src/
```

## Project Structure
```
src/
├── models/          # Pydantic data models
├── repositories/    # DynamoDB data access layer
├── services/        # Business logic
├── api/            # FastAPI route handlers
├── events/         # EventBridge publishing
└── infrastructure/ # AWS CDK infrastructure

tests/
├── unit/           # Pure logic, no dependencies
├── component/      # Components with mocked deps
├── integration/    # Real AWS services
└── e2e/            # Full user journeys
```

## Development Workflow
1. **Test-Driven Development** - Write tests first
2. **Incremental Development** - Small, focused changes
3. **Trunk-Based Development** - Short-lived feature branches
4. **Quality Gates** - 80% test coverage, pre-commit hooks pass

For detailed development instructions, see [claude_instructions.md](claude_instructions.md)
