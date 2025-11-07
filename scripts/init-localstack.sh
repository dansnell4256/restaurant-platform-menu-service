#!/bin/bash
# Script to initialize LocalStack DynamoDB tables for local development

set -e

echo "Waiting for LocalStack to be ready..."
while ! curl -s http://localhost:4566/_localstack/health | grep -q "\"dynamodb\": \"available\""; do
    echo "Waiting for LocalStack DynamoDB..."
    sleep 2
done

echo "LocalStack is ready!"

# Set AWS CLI to use LocalStack
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

ENDPOINT_URL=http://localhost:4566

echo "Creating menu_items table..."
aws dynamodb create-table \
    --endpoint-url $ENDPOINT_URL \
    --table-name menu_items \
    --attribute-definitions \
        AttributeName=restaurant_id,AttributeType=S \
        AttributeName=item_id,AttributeType=S \
    --key-schema \
        AttributeName=restaurant_id,KeyType=HASH \
        AttributeName=item_id,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1

echo "Creating categories table..."
aws dynamodb create-table \
    --endpoint-url $ENDPOINT_URL \
    --table-name categories \
    --attribute-definitions \
        AttributeName=restaurant_id,AttributeType=S \
        AttributeName=category_id,AttributeType=S \
    --key-schema \
        AttributeName=restaurant_id,KeyType=HASH \
        AttributeName=category_id,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1

echo "Tables created successfully!"

# Optional: Add some sample data
echo "Adding sample menu items..."
aws dynamodb put-item \
    --endpoint-url $ENDPOINT_URL \
    --table-name menu_items \
    --item '{
        "restaurant_id": {"S": "rest_001"},
        "item_id": {"S": "item_001"},
        "name": {"S": "Margherita Pizza"},
        "description": {"S": "Classic pizza with tomato sauce, mozzarella, and basil"},
        "price": {"N": "12.99"},
        "category": {"S": "pizza"},
        "availability": {"BOOL": true},
        "allergens": {"L": [{"S": "dairy"}, {"S": "gluten"}]}
    }'

aws dynamodb put-item \
    --endpoint-url $ENDPOINT_URL \
    --table-name menu_items \
    --item '{
        "restaurant_id": {"S": "rest_001"},
        "item_id": {"S": "item_002"},
        "name": {"S": "Caesar Salad"},
        "description": {"S": "Fresh romaine lettuce with Caesar dressing and croutons"},
        "price": {"N": "8.99"},
        "category": {"S": "salad"},
        "availability": {"BOOL": true},
        "allergens": {"L": [{"S": "dairy"}, {"S": "gluten"}]}
    }'

echo "Adding sample categories..."
aws dynamodb put-item \
    --endpoint-url $ENDPOINT_URL \
    --table-name categories \
    --item '{
        "restaurant_id": {"S": "rest_001"},
        "category_id": {"S": "cat_001"},
        "name": {"S": "Appetizers"},
        "display_order": {"N": "1"}
    }'

aws dynamodb put-item \
    --endpoint-url $ENDPOINT_URL \
    --table-name categories \
    --item '{
        "restaurant_id": {"S": "rest_001"},
        "category_id": {"S": "cat_002"},
        "name": {"S": "Main Courses"},
        "display_order": {"N": "2"}
    }'

echo "Sample data added successfully!"
echo ""
echo "LocalStack is ready to use!"
echo "DynamoDB endpoint: http://localhost:4566"
echo ""
echo "To use with the application, set:"
echo "  export DYNAMODB_ENDPOINT=http://localhost:4566"
