#!/usr/bin/env python3
"""
Generate test data for Shopify demo store.
Creates Danish golf products and orders, then syncs to metly database.
"""

import os
import sys
import time
import httpx
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


def generate_access_token(shop: str, client_id: str, client_secret: str) -> str:
    """Generate a fresh Shopify Admin API access token."""
    print("  Generating new access token...")
    response = httpx.post(
        f"https://{shop}/admin/oauth/access_token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}",
        timeout=30.0,
    )
    response.raise_for_status()
    data = response.json()
    print(f"  New token generated (expires in {data.get('expires_in', '?')} seconds)")
    return data["access_token"]


def main():
    load_dotenv("./.env")

    shop = os.getenv("SHOPIFY_STORE")
    client_id = os.getenv("SHOPIFY_API_KEY")
    client_secret = os.getenv("SHOPIFY_API_SECRET")
    db_usr = os.getenv("DB_USR")
    db_pwd = os.getenv("DB_PWD")

    if not shop or not client_id or not client_secret:
        print("Error: SHOPIFY_STORE, SHOPIFY_API_KEY, or SHOPIFY_API_SECRET not set")
        sys.exit(1)

    print("=" * 60)
    print("Shopify Test Data Generator")
    print("=" * 60)

    # Generate fresh access token
    print("\n[0/4] Generating fresh access token...")
    access_token = generate_access_token(shop, client_id, client_secret)

    # Save new token to .env for reference (optional, but helpful)
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        env_content = env_path.read_text()
        if "SHOPIFY_ACCESS_TOKEN=" in env_content:
            new_lines = []
            for line in env_content.splitlines():
                if line.startswith("SHOPIFY_ACCESS_TOKEN="):
                    new_lines.append(f"SHOPIFY_ACCESS_TOKEN={access_token}")
                else:
                    new_lines.append(line)
            env_path.write_text("\n".join(new_lines))
            print("  Updated .env with new token")

    print("\n[1/4] Fetching products with variants...")
    products_df = shopify_get_products(access_token, shop)
    if products_df.empty:
        print("  Error: No products in store")
        sys.exit(1)
    products = products_df.reset_index().to_dict("records")
    print(f"  Found {len(products)} products")

    print("\n[2/4] Creating orders in Shopify...")
    print("  (with rate limit protection - 1 second delay between orders)")
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
