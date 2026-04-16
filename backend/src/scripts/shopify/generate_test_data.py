#!/usr/bin/env python3
"""
Generate test data for Shopify demo store.
Creates Danish golf products and orders, then syncs to metly database.
"""

import os
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from src.integrations.shopify.shopify import (
    create_products as shopify_create_products,
    create_orders as shopify_create_orders,
    get_products as shopify_get_products,
    get_orders as shopify_get_orders,
)
from src.scripts.db.populateDB import populateDB


def main():
    load_dotenv("./.env")

    shop = os.getenv("SHOPIFY_STORE")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    db_usr = os.getenv("DB_USR")
    db_pwd = os.getenv("DB_PWD")

    if not shop or not access_token:
        print("Error: SHOPIFY_STORE or SHOPIFY_ACCESS_TOKEN not set")
        sys.exit(1)

    print("=" * 60)
    print("Shopify Test Data Generator")
    print("=" * 60)

    print("\n[1/4] Fetching products with variants...")
    products_df = shopify_get_products(access_token, shop)
    if products_df.empty:
        print("  Error: No products in store")
        sys.exit(1)
    products = products_df.reset_index().to_dict("records")
    print(f"  Found {len(products)} products")

    print("\n[2/4] Creating orders in Shopify...")
    orders = shopify_create_orders(access_token, shop, products, order_count=15)
    print(f"  Created {len(orders)} orders")

    print("\n[3/4] Syncing to metly database...")
    db_usr_admin = os.getenv("DB_USR_ADMIN")
    db_pwd_admin = os.getenv("DB_PWD_ADMIN")
    populateDB(db_usr_admin, db_pwd_admin)

    print("\n[4/4] Done!")
    print("=" * 60)
    print(f"Created {len(orders)} orders in Shopify")
    print(f"Data synced to metly database")


if __name__ == "__main__":
    main()
