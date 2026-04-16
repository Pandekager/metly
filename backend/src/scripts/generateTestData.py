"""
Shopify Test Data Generator

Generates Danish golf products and orders for testing purposes.
Can run standalone or integrated with main.py CLI.

Usage:
    python generateTestData.py --products 20 --orders 10
    python generateTestData.py --help
"""

import argparse
import os
import random
import sys
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

# Import from shopify.py
from src.integrations.shopify.shopify import (
    DANISH_CITIES,
    DANISH_FIRST_NAMES,
    DANISH_LAST_NAMES,
    create_product,
)

# Load environment
load_dotenv("./.env")

# Danish street types for realistic addresses
DANISH_STREET_TYPES = [
    "Vej",
    "Gade",
    " Boulevard",
    "Allé",
    "Bygade",
    "vej",
    "gade",
]

# Danish product templates organized by category
GOLF_PRODUCT_TEMPLATES = {
    "golf clubs": [
        ("Driver - Pro", "Golfudstyr", 1299.00),
        ("Iron Set - Master", "Golfudstyr", 3499.00),
        ("Putter - Classic", "Golfudstyr", 599.00),
        ("Wedge - Precision", "Golfudstyr", 449.00),
        ("Hybrid - Rescue", "Golfudstyr", 899.00),
    ],
    "golf bags": [
        ("Stand Bag - Lite", "Golfudstyr", 899.00),
        ("Cart Bag - Deluxe", "Golfudstyr", 1299.00),
        ("Travel Bag", "Golfudstyr", 699.00),
    ],
    "golf balls": [
        ("Tour Pro (12 stk)", "Golfudstyr", 299.00),
        ("Practice (50 stk)", "Golfudstyr", 149.00),
        ("Premium (12 stk)", "Golfudstyr", 399.00),
    ],
    "gloves": [
        ("Golfhandske - Herre", "Golfbeklædning", 129.00),
        ("Golfhandske - Dame", "Golfbeklædning", 129.00),
        ("Golfhandske - Junior", "Golfbeklædning", 99.00),
    ],
    "golf apparel": [
        ("Golfcap - Pro", "Golfbeklædning", 199.00),
        ("Golfsko - Herre", "Golfbeklædning", 899.00),
        ("Golfsko - Dame", "Golfbeklædning", 899.00),
        ("Golftrøje - Poloshirt", "Golfbeklædning", 349.00),
        ("Golfvest - Dame", "Golfbeklædning", 599.00),
        ("Golfregnjakke", "Golfbeklædning", 799.00),
    ],
    "accessories": [
        ("Golfhåndklæde", "Golftilbehør", 79.00),
        ("Golfscorekort-holder", "Golftilbehør", 149.00),
        ("Divot-værktøj", "Golftilbehør", 59.00),
        ("Tee-box (100 stk)", "Golftilbehør", 39.00),
        ("Golf洗剂", "Golftilbehør", 49.00),
    ],
}


def _random_danish_name() -> str:
    """Generate a random Danish full name."""
    return f"{random.choice(DANISH_FIRST_NAMES)} {random.choice(DANISH_LAST_NAMES)}"


def _random_danish_address() -> tuple[str, str, str]:
    """Generate a random Danish address (street, city, zip_code)."""
    city, zip_range = random.choice(DANISH_CITIES)
    zip_start, zip_end = zip_range.split("-")
    zip_code = random.randint(int(zip_start), int(zip_end))
    street_num = random.randint(1, 200)
    street_type = random.choice(DANISH_STREET_TYPES)
    street = f"{random.choice(DANISH_FIRST_NAMES) if random.random() > 0.5 else random.choice(DANISH_LAST_NAMES)}{street_type} {street_num}"
    return street, city, str(zip_code)


def generate_danish_customers(count: int) -> list[dict]:
    """
    Generate Danish customer data.

    Args:
        count: Number of customers to generate.

    Returns:
        List of customer dictionaries.
    """
    customers = []
    for i in range(count):
        name = _random_danish_name()
        first_name, last_name = name.split(" ", 1)
        street, city, zip_code = _random_danish_address()
        email = f"{first_name.lower()}.{last_name.lower()}{i}@golfmail.dk"

        customers.append(
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "address": street,
                "city": city,
                "zip_code": zip_code,
            }
        )
    return customers


def generate_products(access_token: str, shop: str, count: int = 20) -> list[dict]:
    """
    Generate golf products in Shopify.

    Args:
        count: Number of products to generate.
        access_token: Shopify access token.
        shop: Shopify shop domain.

    Returns:
        List of created product dictionaries.
    """
    created = []
    templates = []

    # Build template list from categories
    for category, products in GOLF_PRODUCT_TEMPLATES.items():
        for product in products:
            templates.append((category, *product))

    print(f"Generating {count} products...")
    for i in range(count):
        if i < len(templates):
            title, vendor, price = templates[i][1], templates[i][2], templates[i][3]
            category = templates[i][0]
        else:
            # Repeat templates with index if we need more
            template = templates[i % len(templates)]
            title, vendor, price = template[1], template[2], template[3]
            category = template[0]
            title = f"{title} #{i // len(templates) + 1}"

        # Add "Metly Test Golf" prefix to distinguish test products
        full_title = f"[Test] {title}"

        try:
            product = create_product(
                access_token, shop, full_title, category, vendor, price
            )
            created.append(
                {
                    "id": product.get("id"),
                    "title": product.get("title"),
                    "category": category,
                    "price": price,
                }
            )
            print(f"  Created product: {full_title} ({category})")
            time.sleep(0.3)  # Rate limiting
        except Exception as e:
            print(f"  Error creating product {full_title}: {e}")

    print(f"Created {len(created)} products")
    return created


def generate_orders(
    access_token: str,
    shop: str,
    products: list[dict],
    count: int = 10,
    min_total: float = 500.0,
    max_total: float = 5000.0,
) -> list[dict]:
    """
    Generate test orders in Shopify using the created products.

    Args:
        access_token: Shopify access token.
        shop: Shopify shop domain.
        products: List of product dictionaries.
        count: Number of orders to generate.
        min_total: Minimum order total in DKK.
        max_total: Maximum order total in DKK.

    Returns:
        List of created order dictionaries.
    """
    import httpx

    created = []
    if not products:
        print("No products available to create orders with")
        return created

    print(
        f"Generating {count} orders with totals between {min_total}-{max_total} DKK..."
    )

    for i in range(count):
        # Select 1-3 random products
        num_products = random.randint(1, min(3, len(products)))
        selected = random.sample(products, num_products)

        # Calculate line items to achieve target total
        target_total = random.uniform(min_total, max_total)
        line_items = []
        remaining = target_total

        for idx, p in enumerate(selected):
            product_id = p.get("id")
            if not product_id:
                continue

            # Extract numeric ID from gid://shopify/Product/123456789
            numeric_id = product_id.replace("gid://shopify/Product/", "")

            if idx == len(selected) - 1:
                # Last item gets remaining amount
                price = remaining
                quantity = 1
            else:
                # Distribute target across items
                max_per_item = remaining / (len(selected) - idx)
                price = random.uniform(100, min(max_per_item, remaining - 100))
                quantity = random.randint(1, 2)

            line_items.append(
                {
                    "product_id": numeric_id,
                    "quantity": quantity,
                    "price": f"{price:.2f}",
                }
            )
            remaining -= price * quantity

            if remaining <= 0:
                break

        if not line_items:
            continue

        email = f"testkunde{i + 1}@golfmail.dk"

        try:
            # Calculate total for transaction
            total_amount = sum(float(li["price"]) * li["quantity"] for li in line_items)

            response = httpx.post(
                f"https://{shop}/admin/api/2025-10/orders.json",
                headers={
                    "Content-Type": "application/json",
                    "X-Shopify-Access-Token": access_token,
                },
                json={
                    "order": {
                        "line_items": line_items,
                        "email": email,
                        "financial_status": "paid",
                        "transactions": [
                            {
                                "kind": "sale",
                                "status": "success",
                                "amount": f"{total_amount:.2f}",
                            }
                        ],
                    }
                },
                timeout=60.0,
            )

            if response.status_code in (200, 201):
                order = response.json().get("order", {})
                created.append(order)
                print(
                    f"  Created order: {order.get('name', 'Order')} - {total_amount:.2f} DKK"
                )
            else:
                print(f"  Error: {response.status_code} - {response.text[:200]}")

            time.sleep(0.5)  # Rate limiting
        except Exception as e:
            print(f"  Error creating order: {e}")

    print(f"Created {len(created)} orders")
    return created


def run_test_generation(
    products_count: int = 20,
    orders_count: int = 10,
    customers_count: int = 10,
) -> dict:
    """
    Run complete test data generation.

    Args:
        products_count: Number of products to generate.
        orders_count: Number of orders to generate.
        customers_count: Number of customers to generate (for reference).

    Returns:
        Dictionary with generation summary.
    """
    # Get credentials
    shop = os.getenv("SHOPIFY_SHOP")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")

    if not shop or not access_token:
        raise ValueError(
            "Missing Shopify credentials. Set SHOPIFY_SHOP and SHOPIFY_ACCESS_TOKEN in .env"
        )

    print(f"Starting test data generation for: {shop}")
    print(f"Store: Metly Test Golf")
    print("-" * 50)

    # Step 1: Generate customers (for reference/logging)
    customers = generate_danish_customers(customers_count)
    print(f"Generated {len(customers)} customer records")

    # Step 2: Generate products
    products = generate_products(access_token, shop, products_count)
    if not products:
        print("Failed to create products, aborting")
        return {"status": "failed", "reason": "products_failed"}

    # Step 3: Generate orders
    orders = generate_orders(access_token, shop, products, orders_count)

    print("-" * 50)
    print("Test data generation complete!")
    print(f"  Products: {len(products)}")
    print(f"  Orders: {len(orders)}")
    print(f"  Customers: {len(customers)}")

    return {
        "status": "success",
        "products": len(products),
        "orders": len(orders),
        "customers": len(customers),
    }


def cli():
    """Command-line interface for test data generation."""
    parser = argparse.ArgumentParser(
        description="Generate Shopify test data for Metly Test Golf"
    )
    parser.add_argument(
        "--products",
        type=int,
        default=20,
        help="Number of products to generate (default: 20)",
    )
    parser.add_argument(
        "--orders",
        type=int,
        default=10,
        help="Number of orders to generate (default: 10)",
    )
    parser.add_argument(
        "--customers",
        type=int,
        default=10,
        help="Number of customers to generate (default: 10)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without creating",
    )

    args = parser.parse_args()

    if args.dry_run:
        print("Dry run - would generate:")
        print(f"  Products: {args.products}")
        print(f"  Orders: {args.orders}")
        print(f"  Customers: {args.customers}")

        # Show sample data
        print("\nSample customers:")
        customers = generate_danish_customers(3)
        for c in customers:
            print(f"  {c['first_name']} {c['last_name']} <{c['email']}>")

        print("\nProduct categories:")
        for cat in GOLF_PRODUCT_TEMPLATES:
            print(f"  - {cat}")

        return

    # Run generation
    result = run_test_generation(
        products_count=args.products,
        orders_count=args.orders,
        customers_count=args.customers,
    )

    if result.get("status") == "success":
        print("\n✓ Test data generation successful!")
        sys.exit(0)
    else:
        print(f"\n✗ Test data generation failed: {result.get('reason')}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
