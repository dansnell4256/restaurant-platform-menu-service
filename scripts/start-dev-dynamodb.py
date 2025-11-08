#!/usr/bin/env python3
"""Start a local DynamoDB server using moto for development.

This script creates an in-memory DynamoDB server with the required tables
and sample data for local development.

Usage:
    python scripts/start-dev-dynamodb.py
"""

import os
import time
from decimal import Decimal

import boto3
from moto.server import ThreadedMotoServer


def create_tables_and_data(endpoint_url: str) -> None:
    """Create DynamoDB tables and add sample data."""
    # Set dummy credentials for local development
    # These are required by boto3 but not actually used by moto
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"

    dynamodb = boto3.resource("dynamodb", endpoint_url=endpoint_url, region_name="us-east-1")

    # Create menu_items table
    print("Creating menu_items table...")
    menu_items_table = dynamodb.create_table(
        TableName="menu_items",
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

    # Create categories table
    print("Creating categories table...")
    categories_table = dynamodb.create_table(
        TableName="categories",
        KeySchema=[
            {"AttributeName": "restaurant_id", "KeyType": "HASH"},
            {"AttributeName": "category_id", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "restaurant_id", "AttributeType": "S"},
            {"AttributeName": "category_id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Add sample menu items
    print("Adding sample menu items...")
    menu_items_table.put_item(
        Item={
            "restaurant_id": "rest_001",
            "item_id": "item_001",
            "name": "Margherita Pizza",
            "description": "Classic pizza with tomato sauce, mozzarella, and basil",
            "price": Decimal("12.99"),
            "category": "pizza",
            "availability": True,
            "allergens": ["dairy", "gluten"],
        }
    )

    menu_items_table.put_item(
        Item={
            "restaurant_id": "rest_001",
            "item_id": "item_002",
            "name": "Caesar Salad",
            "description": "Fresh romaine lettuce with Caesar dressing and croutons",
            "price": Decimal("8.99"),
            "category": "salad",
            "availability": True,
            "allergens": ["dairy", "gluten"],
        }
    )

    # Add sample categories
    print("Adding sample categories...")
    categories_table.put_item(
        Item={
            "restaurant_id": "rest_001",
            "category_id": "cat_001",
            "name": "Appetizers",
            "display_order": 1,
        }
    )

    categories_table.put_item(
        Item={
            "restaurant_id": "rest_001",
            "category_id": "cat_002",
            "name": "Main Courses",
            "display_order": 2,
        }
    )

    print("✓ Tables and sample data created successfully!")


def main() -> None:
    """Start the moto DynamoDB server."""
    port = int(os.getenv("DYNAMODB_PORT", "5000"))
    endpoint_url = f"http://localhost:{port}"

    print(f"Starting DynamoDB server on port {port}...")
    print(f"Endpoint: {endpoint_url}")
    print("")

    # Start the server in a thread
    server = ThreadedMotoServer(port=port)
    server.start()

    try:
        # Create tables and add data
        create_tables_and_data(endpoint_url)

        print("")
        print("=" * 60)
        print("DynamoDB Server is ready!")
        print("=" * 60)
        print(f"  Endpoint: {endpoint_url}")
        print("  Region: us-east-1")
        print("")
        print("To use with the application, set in your .env:")
        print(f"  DYNAMODB_ENDPOINT={endpoint_url}")
        print("")
        print("Sample data available:")
        print("  - Restaurant: rest_001")
        print("  - Items: item_001, item_002")
        print("  - Categories: cat_001, cat_002")
        print("")
        print("Press Ctrl+C to stop the server")
        print("=" * 60)

        # Keep the server running (ThreadedMotoServer doesn't have join method)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.stop()
        print("Server stopped.")


if __name__ == "__main__":
    main()
