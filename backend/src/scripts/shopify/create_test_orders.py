#!/usr/bin/env python3
"""
Quick test: Create orders in Shopify demo store only.
"""

import os
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from src.integrations.shopify.shopify import get_products, create_orders


def main():
    load_dotenv("./.env")

    shop = os.getenv("SHOPIFY_STORE")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")

    if not shop or not access_token:
        print("Error: Missing config")
        sys.exit(1)

    print("Fetching products...")
    products_df = get_products(access_token, shop)
    products = products_df.reset_index().to_dict("records")
    print(f"Found {len(products)} products")

    print("\nCreating 5 test orders...")
    orders = create_orders(access_token, shop, products, order_count=5)
    print(f"\nDone! Created {len(orders)} orders")
    for o in orders:
        print(f"  - {o.get('name', 'Order')}")


if __name__ == "__main__":
    main()
