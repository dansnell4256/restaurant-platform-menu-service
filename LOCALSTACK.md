# LocalStack Setup for Local Development

This guide shows you how to run the Menu Service locally with LocalStack, which provides a fully functional local AWS environment.

## Prerequisites

- Docker Desktop installed and running
- AWS CLI installed (`brew install awscli` on macOS)

## Quick Start

### 1. Start LocalStack

```bash
# Start LocalStack using Docker Compose
docker compose up -d

# Check that LocalStack is running
curl http://localhost:4566/_localstack/health
```

### 2. Initialize DynamoDB Tables

```bash
# Run the initialization script
./scripts/init-localstack.sh
```

This script will:
- Create the `menu_items` and `categories` DynamoDB tables
- Add sample data for testing
- Configure tables with the correct schema

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# The .env file should have:
# DYNAMODB_ENDPOINT=http://localhost:4566
# API_KEYS=dev-key-123,test-key-456
#
# Optional: Configure API key permissions for restaurant access control
# Leave API_KEY_PERMISSIONS empty to allow all keys to access all restaurants (legacy mode)
# Or set permissions like: API_KEY_PERMISSIONS=dev-key-123:rest_001;admin-key:*
```

### 4. Start the API Server

```bash
# Activate your virtual environment
source venv/bin/activate

# Start the server
uvicorn src.main:app --reload --port 8000
```

### 5. Test the API

Open your browser to http://localhost:8000/docs

Try these requests:
1. Click "Authorize" and enter API key: `dev-key-123`
2. Try GET `/menus/rest_001/items` to see sample menu items
3. Try GET `/menus/rest_001/categories` to see sample categories

## Working with LocalStack DynamoDB

### View Tables

```bash
aws dynamodb list-tables \
    --endpoint-url http://localhost:4566 \
    --region us-east-1
```

### Query Items

```bash
# List all items for a restaurant
aws dynamodb query \
    --endpoint-url http://localhost:4566 \
    --table-name menu_items \
    --key-condition-expression "restaurant_id = :rid" \
    --expression-attribute-values '{":rid":{"S":"rest_001"}}' \
    --region us-east-1
```

### Scan Entire Table

```bash
aws dynamodb scan \
    --endpoint-url http://localhost:4566 \
    --table-name menu_items \
    --region us-east-1
```

### Add More Sample Data

```bash
aws dynamodb put-item \
    --endpoint-url http://localhost:4566 \
    --table-name menu_items \
    --item '{
        "restaurant_id": {"S": "rest_001"},
        "item_id": {"S": "item_003"},
        "name": {"S": "Spaghetti Carbonara"},
        "description": {"S": "Creamy pasta with bacon and parmesan"},
        "price": {"N": "14.99"},
        "category": {"S": "pasta"},
        "availability": {"BOOL": true},
        "allergens": {"L": [{"S": "dairy"}, {"S": "gluten"}]}
    }'
```

## Stopping and Cleaning Up

```bash
# Stop LocalStack
docker compose down

# Remove all data (start fresh)
docker compose down -v
rm -rf localstack-data
```

## Troubleshooting

### LocalStack not starting

```bash
# Check Docker is running
docker ps

# Check LocalStack logs
docker compose logs localstack
```

### Tables not created

```bash
# Run the init script again
./scripts/init-localstack.sh

# Or create tables manually
aws dynamodb create-table \
    --endpoint-url http://localhost:4566 \
    --table-name menu_items \
    --attribute-definitions \
        AttributeName=restaurant_id,AttributeType=S \
        AttributeName=item_id,AttributeType=S \
    --key-schema \
        AttributeName=restaurant_id,KeyType=HASH \
        AttributeName=item_id,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST
```

### Cannot connect to DynamoDB

Make sure:
1. LocalStack is running: `docker compose ps`
2. Port 4566 is not in use: `lsof -i :4566`
3. Environment variable is set: `echo $DYNAMODB_ENDPOINT`
4. `.env` file has `DYNAMODB_ENDPOINT=http://localhost:4566`

## LocalStack Web UI (Optional)

LocalStack Pro provides a web UI at http://localhost:4566/_localstack/health

For the free version, you can use the AWS CLI or third-party tools like:
- DynamoDB Admin: `npm install -g dynamodb-admin`
- NoSQL Workbench for Amazon DynamoDB

## API Key Permissions (Optional)

The Menu Service supports restaurant-level access control for API keys. This allows you to restrict which restaurants each API key can access.

### Configuration

Set the `API_KEY_PERMISSIONS` environment variable in your `.env` file:

```bash
# Format: KEY1:rest_001,rest_002;KEY2:rest_003;ADMIN_KEY:*
API_KEY_PERMISSIONS=dev-key-123:rest_001;admin-key:*
```

### Permission Rules

- **Specific Restaurants**: List restaurant IDs separated by commas
  - Example: `dev-key-123:rest_001,rest_002` - Can only access rest_001 and rest_002
- **Wildcard Access**: Use `*` to grant access to all restaurants
  - Example: `admin-key:*` - Can access any restaurant
- **Legacy Mode**: Leave `API_KEY_PERMISSIONS` empty or unset
  - All valid API keys can access all restaurants (backward compatible)

### Examples

```bash
# Single restaurant access
API_KEY_PERMISSIONS=partner-key-abc:rest_001

# Multiple restaurants
API_KEY_PERMISSIONS=partner-key-abc:rest_001,rest_002,rest_003

# Admin key with wildcard
API_KEY_PERMISSIONS=admin-key:*

# Mixed permissions (semicolon-separated)
API_KEY_PERMISSIONS=partner-key-abc:rest_001;partner-key-xyz:rest_002;admin-key:*

# Legacy mode (no restrictions)
API_KEY_PERMISSIONS=
```

### Authorization Errors

If an API key tries to access a restaurant it doesn't have permission for:

```bash
curl http://localhost:8000/menus/rest_002/items \
  -H "X-API-Key: dev-key-123"

# Response: 403 Forbidden
{
  "detail": "API key is not authorized to access restaurant rest_002"
}
```

## Benefits of LocalStack

✅ **Fast Development** - No AWS latency, instant feedback
✅ **Cost Free** - No AWS charges for development
✅ **Offline Work** - Develop without internet connection
✅ **Isolated Testing** - Each developer has their own environment
✅ **Easy Reset** - Wipe data and start fresh anytime
✅ **CI/CD Ready** - Use in automated testing pipelines
