import random
import pandas as pd
import pymysql
from datetime import datetime, timedelta
from typing import Dict, List
import uuid


# Golf equipment product catalog with categories and realistic pricing
GOLF_PRODUCTS = {
    "Drivere": [
        {"name": "TaylorMade Stealth 2", "price": 4999, "cost": 3000},
        {"name": "Callaway Paradym", "price": 5299, "cost": 3200},
        {"name": "Titleist TSR3", "price": 5499, "cost": 3300},
        {"name": "Ping G430 MAX", "price": 4799, "cost": 2900},
        {"name": "Cobra LTDx LS", "price": 4299, "cost": 2600},
    ],
    "Fairway Træer": [
        {"name": "TaylorMade Stealth 2 3-Træ", "price": 2999, "cost": 1800},
        {"name": "Callaway Paradym 5-Træ", "price": 2799, "cost": 1700},
        {"name": "Titleist TSR2 3-Træ", "price": 3199, "cost": 1900},
        {"name": "Ping G430 5-Træ", "price": 2899, "cost": 1750},
    ],
    "Hybrider": [
        {"name": "TaylorMade Stealth 2 Hybrid", "price": 2299, "cost": 1400},
        {"name": "Callaway Apex Hybrid", "price": 2499, "cost": 1500},
        {"name": "Titleist TSR3 Hybrid", "price": 2699, "cost": 1600},
        {"name": "Ping G430 Hybrid", "price": 2399, "cost": 1450},
    ],
    "Jernsæt": [
        {"name": "TaylorMade P790 Jern (4-PW)", "price": 10999, "cost": 6600},
        {"name": "Callaway Paradym Jern (5-PW)", "price": 11499, "cost": 6900},
        {"name": "Titleist T200 Jern (4-PW)", "price": 12999, "cost": 7800},
        {"name": "Ping i530 Jern (5-PW)", "price": 10499, "cost": 6300},
        {"name": "Mizuno JPX923 Hot Metal (5-PW)", "price": 9999, "cost": 6000},
    ],
    "Wedges": [
        {"name": "Titleist Vokey SM9 52°", "price": 1499, "cost": 900},
        {"name": "Cleveland RTX ZipCore 56°", "price": 1399, "cost": 840},
        {"name": "Callaway Jaws Raw 60°", "price": 1449, "cost": 870},
        {"name": "TaylorMade Milled Grind 3 58°", "price": 1549, "cost": 930},
    ],
    "Puttere": [
        {"name": "Scotty Cameron Newport 2", "price": 4499, "cost": 2700},
        {"name": "TaylorMade Spider GT", "price": 3999, "cost": 2400},
        {"name": "Odyssey Tri-Hot 5K", "price": 2499, "cost": 1500},
        {"name": "Ping Anser 2D", "price": 2999, "cost": 1800},
        {"name": "Cleveland Huntington Beach", "price": 1999, "cost": 1200},
    ],
    "Golfbolde": [
        {"name": "Titleist Pro V1 (Dusin)", "price": 549, "cost": 330},
        {"name": "Callaway Chrome Soft (Dusin)", "price": 499, "cost": 300},
        {"name": "TaylorMade TP5 (Dusin)", "price": 529, "cost": 317},
        {"name": "Srixon Z-Star (Dusin)", "price": 479, "cost": 287},
        {"name": "Bridgestone Tour B XS (Dusin)", "price": 499, "cost": 300},
    ],
    "Golftasker": [
        {"name": "Titleist Players 4 StaDry Stand Taske", "price": 2999, "cost": 1800},
        {"name": "Callaway ORG 14 Cart Taske", "price": 3499, "cost": 2100},
        {"name": "TaylorMade FlexTech Stand Taske", "price": 1999, "cost": 1200},
        {"name": "Ping Hoofer 14 Stand Taske", "price": 2799, "cost": 1680},
    ],
    "Golfhandsker": [
        {"name": "FootJoy StaSof Handske", "price": 249, "cost": 150},
        {"name": "Titleist Players Handske", "price": 299, "cost": 180},
        {"name": "Callaway Dawn Patrol Handske", "price": 199, "cost": 120},
        {"name": "TaylorMade Tour Preferred Handske", "price": 279, "cost": 167},
    ],
    "Golfsko": [
        {"name": "FootJoy Pro/SL", "price": 1799, "cost": 1080},
        {"name": "Adidas Tour360 22", "price": 1999, "cost": 1200},
        {"name": "Nike Air Zoom Infinity Tour", "price": 2199, "cost": 1320},
        {"name": "ECCO Biom H4", "price": 2499, "cost": 1500},
    ],
    "Afstandsmålere": [
        {"name": "Bushnell Tour V5", "price": 3499, "cost": 2100},
        {"name": "Garmin Approach Z82", "price": 5999, "cost": 3600},
        {"name": "Precision Pro NX9", "price": 2799, "cost": 1680},
    ],
    "GPS Ure": [
        {"name": "Garmin Approach S62", "price": 4999, "cost": 3000},
        {"name": "Shot Scope V3", "price": 2999, "cost": 1800},
        {"name": "Bushnell Ion Elite", "price": 1999, "cost": 1200},
    ],
    "Træningshjælpemidler": [
        {"name": "SKLZ Gold Flex Træner", "price": 699, "cost": 420},
        {"name": "Orange Whip Træner", "price": 1099, "cost": 660},
        {"name": "PuttOut Pressure Træner", "price": 299, "cost": 180},
        {"name": "Alignment Stick Sæt", "price": 349, "cost": 210},
    ],
    "Golftøj": [
        {"name": "Nike Dri-FIT Polo", "price": 599, "cost": 360},
        {"name": "FootJoy Performance Bukser", "price": 899, "cost": 540},
        {"name": "Adidas Golf Jakke", "price": 1299, "cost": 780},
        {"name": "Under Armour Golf Shorts", "price": 699, "cost": 420},
    ],
    "Golftilbehør": [
        {"name": "Golf Tees Pakke (50)", "price": 79, "cost": 47},
        {"name": "Boldmarkør Sæt", "price": 149, "cost": 89},
        {"name": "Golf Håndklæde Premium", "price": 249, "cost": 150},
        {"name": "Divot Værktøj med Markør", "price": 129, "cost": 77},
    ],
}

# Danish customer data pools
FIRST_NAMES = [
    "Anders",
    "Lars",
    "Morten",
    "Peter",
    "Henrik",
    "Jesper",
    "Thomas",
    "Michael",
    "Søren",
    "Kasper",
    "Martin",
    "Christian",
    "Rasmus",
    "Mads",
    "Jens",
    "Mikkel",
    "Anne",
    "Mette",
    "Kirsten",
    "Hanne",
    "Susanne",
    "Lene",
    "Camilla",
    "Maria",
    "Louise",
    "Sarah",
    "Julie",
    "Emma",
    "Ida",
    "Sofie",
    "Caroline",
    "Laura",
]

LAST_NAMES = [
    "Jensen",
    "Nielsen",
    "Hansen",
    "Pedersen",
    "Andersen",
    "Christensen",
    "Larsen",
    "Sørensen",
    "Rasmussen",
    "Jørgensen",
    "Petersen",
    "Madsen",
    "Kristensen",
    "Olsen",
    "Thomsen",
    "Christiansen",
    "Poulsen",
    "Johansen",
    "Møller",
    "Mortensen",
]

CITIES = [
    {"city": "København", "zip": "2100"},
    {"city": "Aarhus", "zip": "8000"},
    {"city": "Odense", "zip": "5000"},
    {"city": "Aalborg", "zip": "9000"},
    {"city": "Esbjerg", "zip": "6700"},
    {"city": "Randers", "zip": "8900"},
    {"city": "Kolding", "zip": "6000"},
    {"city": "Horsens", "zip": "8700"},
    {"city": "Vejle", "zip": "7100"},
    {"city": "Roskilde", "zip": "4000"},
    {"city": "Herning", "zip": "7400"},
    {"city": "Silkeborg", "zip": "8600"},
    {"city": "Næstved", "zip": "4700"},
    {"city": "Fredericia", "zip": "7000"},
    {"city": "Viborg", "zip": "8800"},
]

STREET_NAMES = [
    "Vestergade",
    "Østergade",
    "Nørregade",
    "Søndergade",
    "Hovedgaden",
    "Kirkevej",
    "Skolevej",
    "Birkevej",
    "Skovvej",
    "Strandvejen",
]

# Sales trends by month (multiplier for base sales volume)
MONTHLY_TRENDS = {
    1: 0.6,  # January - slow
    2: 0.7,  # February - picking up
    3: 1.2,  # March - spring prep
    4: 1.5,  # April - season start
    5: 1.8,  # May - peak season
    6: 1.9,  # June - peak season
    7: 1.7,  # July - summer high
    8: 1.6,  # August - still high
    9: 1.3,  # September - winding down
    10: 0.9,  # October - slower
    11: 0.8,  # November - off-season
    12: 1.1,  # December - holiday gifts
}

# Category popularity (affects sales frequency)
CATEGORY_POPULARITY = {
    "Golfbolde": 3.0,
    "Golfhandsker": 2.5,
    "Golftilbehør": 2.0,
    "Golftøj": 1.8,
    "Wedges": 1.5,
    "Puttere": 1.3,
    "Træningshjælpemidler": 1.2,
    "Jernsæt": 1.0,
    "Drivere": 1.0,
    "Golfsko": 0.9,
    "Fairway Træer": 0.8,
    "Hybrider": 0.7,
    "Golftasker": 0.6,
    "Afstandsmålere": 0.5,
    "GPS Ure": 0.4,
}


def _generate_customer_id() -> str:
    """Generate a unique customer ID."""
    return f"DEMO_CUST_{uuid.uuid4().hex[:12]}"


def _generate_order_id() -> str:
    """Generate a unique order ID."""
    return f"DEMO_ORD_{uuid.uuid4().hex[:12]}"


def _generate_order_line_id() -> str:
    """Generate a unique order line ID."""
    return f"DEMO_LINE_{uuid.uuid4().hex[:12]}"


def _generate_product_id(category: str, product_name: str) -> str:
    """Generate a deterministic product ID."""
    # Use hash to make it deterministic but unique
    hash_val = hash(f"{category}_{product_name}") & 0x7FFFFFFF
    return f"DEMO_PROD_{hash_val}"


def _generate_category_id(category: str) -> str:
    """Generate a deterministic category ID."""
    hash_val = hash(category) & 0x7FFFFFFF
    return f"DEMO_CAT_{hash_val}"


def _generate_customer() -> Dict:
    """Generate a random Danish customer."""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    location = random.choice(CITIES)
    street_number = random.randint(1, 150)
    street_name = random.choice(STREET_NAMES)

    return {
        "id": _generate_customer_id(),
        "billing_firstName": first_name,
        "billing_lastName": last_name,
        "billing_addressLine": f"{street_name} {street_number}",
        "billing_city": location["city"],
        "billing_zipCode": location["zip"],
        "billing_email": f"{first_name.lower()}.{last_name.lower()}@example.dk",
        "extended_internal": None,
        "extended_external": None,
    }


def _get_daily_order_count(date: datetime) -> int:
    """Calculate how many orders should be generated for a given date."""
    month = date.month
    month_trend = MONTHLY_TRENDS.get(month, 1.0)

    # Weekend boost (Saturday and Sunday)
    weekday = date.weekday()
    if weekday in [5, 6]:  # Saturday, Sunday
        weekend_boost = 1.3
    else:
        weekend_boost = 1.0

    # Base orders per day: 5-15
    base_orders = random.randint(5, 15)

    # Apply trends
    daily_orders = int(base_orders * month_trend * weekend_boost)

    return max(1, daily_orders)  # At least 1 order per day


def _select_products_for_order(date: datetime) -> List[Dict]:
    """Select products for an order with realistic patterns."""
    products = []
    num_items = random.choices(
        [1, 2, 3, 4, 5],
        weights=[40, 30, 15, 10, 5],
        k=1,  # Most orders have 1-2 items
    )[0]

    month = date.month

    for _ in range(num_items):
        # Select category based on popularity and season
        categories = list(GOLF_PRODUCTS.keys())
        weights = [CATEGORY_POPULARITY.get(cat, 1.0) for cat in categories]

        # Boost certain categories in specific months
        if month in [3, 4, 5]:  # Spring - boost clubs
            for i, cat in enumerate(categories):
                if cat in ["Drivere", "Jernsæt", "Fairway Træer"]:
                    weights[i] *= 1.5
        elif month in [12]:  # December - boost accessories/gifts
            for i, cat in enumerate(categories):
                if cat in ["Golftilbehør", "Golfbolde", "Træningshjælpemidler"]:
                    weights[i] *= 2.0

        category = random.choices(categories, weights=weights, k=1)[0]
        product_list = GOLF_PRODUCTS[category]
        product = random.choice(product_list)

        # Quantity - usually 1, sometimes 2-3 for consumables
        if category in ["Golfbolde", "Golfhandsker", "Golftilbehør"]:
            quantity = random.choices([1, 2, 3], weights=[60, 30, 10], k=1)[0]
        else:
            quantity = 1

        products.append(
            {
                "category": category,
                "product": product,
                "quantity": quantity,
            }
        )

    return products


def makeDummyData(conn: pymysql.Connection, user_id):
    """
    Generate dummy golf equipment sales data for demo tenant.
    This function deletes all existing demo data and generates fresh data for the past year.

    Args:
        conn: Database connection
        user_id: The tenant/user ID
    """
    print(
        f"\n=== Generating Demo Data for Golf Equipment Shop (user_id: {user_id}) ==="
    )

    # Delete all existing data for this demo user (in correct order to respect FK constraints)
    print("Deleting existing demo data...")
    try:
        with conn.cursor() as cursor:
            # Delete in reverse order of foreign key dependencies
            cursor.execute("DELETE FROM order_lines WHERE user_id = %s", (user_id,))
            deleted_order_lines = cursor.rowcount
            cursor.execute("DELETE FROM orders WHERE user_id = %s", (user_id,))
            deleted_orders = cursor.rowcount
            cursor.execute("DELETE FROM customers WHERE user_id = %s", (user_id,))
            deleted_customers = cursor.rowcount
            cursor.execute("DELETE FROM products WHERE user_id = %s", (user_id,))
            deleted_products = cursor.rowcount
            cursor.execute(
                "DELETE FROM product_categories WHERE user_id = %s", (user_id,)
            )
            deleted_categories = cursor.rowcount
            cursor.execute("DELETE FROM languages WHERE user_id = %s", (user_id,))
            deleted_languages = cursor.rowcount

            print(
                f"  Deleted: {deleted_order_lines} order lines, {deleted_orders} orders, "
                f"{deleted_customers} customers, {deleted_products} products, "
                f"{deleted_categories} categories, {deleted_languages} languages"
            )
    except Exception as e:
        print(f"Warning: Could not delete existing data: {e}")

    # Generate data for the past year
    end_date = datetime.now()
    start_date = datetime(end_date.year - 1, 1, 1)  # January 1st of last year
    print(
        f"Generating fresh data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )

    # Generate all products and categories first
    all_products = []
    all_categories = []

    for category, products in GOLF_PRODUCTS.items():
        category_id = _generate_category_id(category)

        # Add category
        all_categories.append(
            {
                "id": category_id,
                "path": f"/golf-equipment/{category.lower().replace(' ', '-')}",
                "title": category,
                "createdAt": start_date.strftime("%Y-%m-%d %H:%M:%S"),
                "updatedAt": end_date.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Add products
        for product in products:
            product_id = _generate_product_id(category, product["name"])
            all_products.append(
                {
                    "id": product_id,
                    "product_name": product["name"],
                    "subcategory_id": category_id,
                    "subcategory_name": category,
                    "maincategory_id": category_id,
                    "maincategory_name": category,
                }
            )

    # Insert product categories
    if all_categories:
        print(f"Inserting {len(all_categories)} product categories")
        with conn.cursor() as cursor:
            insert_sql = """
                INSERT INTO product_categories (id, user_id, path, title, createdAt, updatedAt)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = [
                (
                    cat["id"],
                    user_id,
                    cat["path"],
                    cat["title"],
                    cat["createdAt"],
                    cat["updatedAt"],
                )
                for cat in all_categories
            ]
            cursor.executemany(insert_sql, params)

    # Insert products
    if all_products:
        print(f"Inserting {len(all_products)} products")
        with conn.cursor() as cursor:
            insert_sql = """
                INSERT INTO products (id, user_id, product_name, subcategory_id, subcategory_name, 
                                     maincategory_id, maincategory_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            params = [
                (
                    p["id"],
                    user_id,
                    p["product_name"],
                    p["subcategory_id"],
                    p["subcategory_name"],
                    p["maincategory_id"],
                    p["maincategory_name"],
                )
                for p in all_products
            ]
            cursor.executemany(insert_sql, params)

    # Generate language (Danish)
    language_id = "da-DK"
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO languages (id, user_id, iso)
            VALUES (%s, %s, %s)
        """,
            (language_id, user_id, "da"),
        )

    # Generate orders day by day
    customers_map = {}
    all_orders = []
    all_order_lines = []

    current_date = start_date
    total_orders_generated = 0

    while current_date.date() <= end_date.date():
        daily_orders = _get_daily_order_count(current_date)

        for _ in range(daily_orders):
            # Decide if this is a new customer or returning (70% returning)
            if customers_map and random.random() < 0.7:
                customer = random.choice(list(customers_map.values()))
            else:
                customer = _generate_customer()
                customers_map[customer["id"]] = customer

            # Generate order
            order_id = _generate_order_id()
            order_time = current_date.replace(
                hour=random.randint(8, 20),
                minute=random.randint(0, 59),
                second=random.randint(0, 59),
            )

            # Select products for this order
            selected_products = _select_products_for_order(current_date)

            # Calculate order totals
            total_items = sum(p["quantity"] for p in selected_products)
            total_amount = 0

            # Generate order lines
            for product_item in selected_products:
                order_line_id = _generate_order_line_id()
                category = product_item["category"]
                product = product_item["product"]
                quantity = product_item["quantity"]
                product_id = _generate_product_id(category, product["name"])

                unit_price = product["price"]
                unit_cost = product["cost"]
                total_amount += unit_price * quantity

                all_order_lines.append(
                    {
                        "order_line_id": order_line_id,
                        "order_id": order_id,
                        "product_id": product_id,
                        "product_title": product["name"],
                        "variant_title": None,
                        "amount": quantity,
                        "unit_revenue": unit_price,
                        "unit_cost": unit_cost,
                        "stock_status": "in_stock",
                        "stock_amount": str(random.randint(10, 100)),
                    }
                )

            all_orders.append(
                {
                    "id": order_id,
                    "totalItems": total_items,
                    "total": total_amount,
                    "currency_symbol": "DKK",
                    "createdAt": order_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "customer_id": customer["id"],
                    "language_id": language_id,
                    "referrer": random.choice(
                        [
                            "https://www.google.com/",
                            "https://www.facebook.com/",
                            "https://www.instagram.com/",
                            "direct",
                            None,
                        ]
                    ),
                    # Order status for revenue leak analysis
                    # 3% payment_failed, 5% cancelled, 2% refunded
                    "orderStatus": (
                        "payment_failed"
                        if random.random() < 0.03
                        else "cancelled"
                        if random.random() < 0.05
                        else "refunded"
                        if random.random() < 0.02
                        else "completed"
                    ),
                    # Order flow analysis fields
                    "processed_at": (
                        order_time + timedelta(hours=random.randint(1, 12))
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    if random.random() > 0.1
                    else None,
                    "fulfilled_at": (
                        order_time
                        + timedelta(
                            days=random.randint(1, 5), hours=random.randint(0, 23)
                        )
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    if random.random() > 0.1
                    else None,
                    "cancelled_at": (
                        order_time + timedelta(days=random.randint(1, 3))
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    if random.random() < 0.05  # Same as cancelled status
                    else None,
                    "closed_at": (
                        order_time + timedelta(days=random.randint(5, 14))
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    if random.random() > 0.15
                    else None,
                    "fulfillment_status": "fulfilled"
                    if random.random() > 0.1
                    else ("cancelled" if random.random() > 0.8 else "pending"),
                    "tracking_number": f"TRK{random.randint(100000, 999999)}"
                    if random.random() > 0.1
                    else None,
                    "carrier": random.choice(["PostNord", "GLS", "DAO", "Bring"])
                    if random.random() > 0.1
                    else None,
                }
            )

            total_orders_generated += 1

        current_date += timedelta(days=1)

    print(
        f"Generated {total_orders_generated} orders with {len(all_order_lines)} order lines"
    )
    print(f"Total unique customers: {len(customers_map)}")

    # Insert customers
    if customers_map:
        print(f"Inserting {len(customers_map)} customers")
        with conn.cursor() as cursor:
            insert_sql = """
                INSERT INTO customers (id, user_id, billing_firstName, billing_lastName,
                                      billing_addressLine, billing_city, billing_zipCode, 
                                      billing_email, extended_internal, extended_external)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = [
                (
                    c["id"],
                    user_id,
                    c["billing_firstName"],
                    c["billing_lastName"],
                    c["billing_addressLine"],
                    c["billing_city"],
                    c["billing_zipCode"],
                    c["billing_email"],
                    c["extended_internal"],
                    c["extended_external"],
                )
                for c in customers_map.values()
            ]
            cursor.executemany(insert_sql, params)

    # Insert orders
    if all_orders:
        print(f"Inserting {len(all_orders)} orders")
        with conn.cursor() as cursor:
            insert_sql = """
                INSERT INTO orders (id, user_id, totalItems, total, currency_symbol,
                                   createdAt, customer_id, language_id, referrer,
                                   orderStatus, cancelledAt)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = [
                (
                    o["id"],
                    user_id,
                    o["totalItems"],
                    o["total"],
                    o["currency_symbol"],
                    o["createdAt"],
                    o["customer_id"],
                    o["language_id"],
                    o["referrer"],
                    o.get("orderStatus", "completed"),
                    o.get("cancelledAt"),
                )
                for o in all_orders
            ]
            cursor.executemany(insert_sql, params)

    # Insert order lines
    if all_order_lines:
        print(f"Inserting {len(all_order_lines)} order lines")
        with conn.cursor() as cursor:
            insert_sql = """
                INSERT INTO order_lines (order_line_id, user_id, order_id, product_id,
                                        product_title, variant_title, amount, unit_revenue,
                                        unit_cost, stock_status, stock_amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = [
                (
                    ol["order_line_id"],
                    user_id,
                    ol["order_id"],
                    ol["product_id"],
                    ol["product_title"],
                    ol["variant_title"],
                    ol["amount"],
                    ol["unit_revenue"],
                    ol["unit_cost"],
                    ol["stock_status"],
                    ol["stock_amount"],
                )
                for ol in all_order_lines
            ]
            # Insert in chunks
            chunk_size = 1000
            for i in range(0, len(params), chunk_size):
                chunk = params[i : i + chunk_size]
                cursor.executemany(insert_sql, chunk)

    print("=== Demo Data Generation Complete ===\n")


if __name__ == "__main__":
    # Test the function
    from dotenv import load_dotenv
    import os
    from urllib.parse import quote_plus

    load_dotenv("./.env")
    db_usr = os.getenv("DB_USR_ADMIN")
    db_pwd = os.getenv("DB_PWD_ADMIN")

    if db_usr and db_pwd:
        conn = pymysql.connect(
            host="metly.dk",
            port=3306,
            user=db_usr,
            password=db_pwd,
            database="metlydk_main",
            connect_timeout=10,
        )

        # Use a test user_id - replace with actual demo user UUID
        test_user_id = "demo-user-test-123"
        makeDummyData(conn, test_user_id)

        conn.commit()
        conn.close()
    else:
        print("Database credentials not found!")
