from dotenv import load_dotenv
import os
import pymysql
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.integrations.dandomain.modern import (
    getDandomainToken,
    getOrders as ModernGetOrders,
    getProductCategories,
)

from src.integrations.dandomain.classic import (
    getOrders as ClassicGetOrders,
    getProducts as ClassicGetProducts,
)

from src.integrations.demo.demo import makeDummyData
from src.integrations.shopify.shopify import (
    get_orders as ShopifyGetOrders,
    get_products as ShopifyGetProducts,
)

# load .env
load_dotenv("./.env")
db_usr = os.getenv("DB_USR_ADMIN")
db_pwd = os.getenv("DB_PWD_ADMIN")


def connectDB(db_usr, db_pwd):
    if not db_usr or not db_pwd:
        logger.error("Database credentials not found in environment variable!")
        return None, None

    import time

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            # Create a SQLAlchemy engine (used by pandas.read_sql_query to avoid warnings)
            user_quoted = quote_plus(db_usr)
            pwd_quoted = quote_plus(db_pwd)
            database_url = (
                f"mysql+pymysql://{user_quoted}:{pwd_quoted}@metly.dk:3306/metlydk_main"
            )
            connect_args = {
                "connect_timeout": 10,
                "read_timeout": 30,
                "write_timeout": 30,
            }
            engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_size=5,
                max_overflow=10,
                connect_args=connect_args,
            )
            conn = pymysql.connect(
                host="metly.dk",
                port=3306,
                user=db_usr,
                password=db_pwd,
                database="metlydk_main",
                connect_timeout=10,
                read_timeout=30,
                write_timeout=30,
            )
            try:
                setattr(conn, "_sqlalchemy_engine", engine)
            except Exception:
                logger.debug(
                    "Failed to attach _sqlalchemy_engine attribute to raw connection"
                )
                pass
            stmt = """
                    SELECT u.*, p.name AS platform_name
                    FROM users u
                    JOIN platforms p 
                        ON u.platform_id = p.id;
                    """
            with conn.cursor() as cursor:
                cursor.execute(stmt)
                users = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                df_users = pd.DataFrame(users, columns=columns)
            logger.info("Connected to DB and fetched users: %d", len(df_users))
            return conn, df_users
        except BrokenPipeError as e:
            logger.error("BrokenPipeError on DB connect: %s", str(e))
            if attempt < max_retries:
                time.sleep(2)
                continue
            else:
                return None, None
        except Exception as e:
            logger.error("Connection failed: %s", str(e))
            if attempt < max_retries:
                time.sleep(2)
                continue
            else:
                return None, None


def populateDB(db_usr, db_pwd):

    try:
        conn, df_users = connectDB(db_usr, db_pwd)
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # Ensure we actually have a DB connection and users
    if conn is None:
        print("No database connection established. Nothing to do.")
        return

    if df_users is None or df_users.empty:
        print("No users fetched from the remote database. Nothing to do.")
        return

    try:
        # Summary for inserted rows. Cursors are created as needed using context managers
        # to avoid holding many open cursors at once.
        summary = {
            "customers": 0,
            "products": 0,
            "languages": 0,
            "orders": 0,
            "product_categories": 0,
            "order_lines": 0,
        }

        for idx, row in df_users.iterrows():
            if row.get("platform_name") == "Dandomain Modern":

                tenant = row.get("tenant")
                client_id = row.get("client_id")
                client_secret = row.get("client_secret")
                print(f"Fetching token for {row.get('username')}")
                token = getDandomainToken(tenant, client_id, client_secret)
                orders = ModernGetOrders(token, tenant)
                product_categories = getProductCategories(token, tenant)

                # Delete existing rows for this user in child->parent order to avoid FK constraint errors
                # Do this once per user before inserting fresh data
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            f"DELETE FROM order_lines WHERE user_id = '{row.get('id')}';"
                        )
                        cursor.execute(
                            f"DELETE FROM orders WHERE user_id = '{row.get('id')}';"
                        )
                        cursor.execute(
                            f"DELETE FROM product_categories WHERE user_id = '{row.get('id')}';"
                        )
                        cursor.execute(
                            f"DELETE FROM customers WHERE user_id = '{row.get('id')}';"
                        )
                        cursor.execute(
                            f"DELETE FROM languages WHERE user_id = '{row.get('id')}';"
                        )
                except Exception as e:
                    print(
                        f"  Warning: failed to delete existing rows for user id='{row.get('id')}': {e}"
                    )

                # Insert customers
                df_customers = orders.get("customers")
                if df_customers is not None and not df_customers.empty:
                    print(f"  Inserting {len(df_customers)} customers")

                    # customers table cleared above
                    # helper to convert pandas NA to SQL NULL
                    def _sql_val(v):
                        return None if pd.isna(v) else v

                    params = [
                        (
                            cust_row.name,
                            row.get("id"),
                            _sql_val(cust_row.get("billing_firstName")),
                            _sql_val(cust_row.get("billing_lastName")),
                            _sql_val(cust_row.get("billing_addressLine")),
                            _sql_val(cust_row.get("billing_city")),
                            _sql_val(cust_row.get("billing_zipCode")),
                            _sql_val(cust_row.get("billing_email")),
                            _sql_val(cust_row.get("extended_internal")),
                            _sql_val(cust_row.get("extended_external")),
                        )
                        for _, cust_row in df_customers.iterrows()
                    ]

                    insert_sql = """
                        INSERT INTO customers (
                            id, user_id, billing_firstName, billing_lastName,
                            billing_addressLine, billing_city, billing_zipCode, billing_email, extended_internal, extended_external
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """

                    chunk_size = 1000
                    with conn.cursor() as cursor:
                        for i in range(0, len(params), chunk_size):
                            chunk = params[i : i + chunk_size]
                            cursor.executemany(insert_sql, chunk)
                            summary["customers"] += len(chunk)
                else:
                    print("  No customers to insert")

                # Insert languages
                df_languages = orders.get("languages")
                if df_languages is not None and not df_languages.empty:
                    print(f"  Inserting {len(df_languages)} languages")
                    # languages table cleared above
                    params = [
                        (
                            lang_row.name,
                            row.get("id"),
                            (
                                None
                                if pd.isna(lang_row.get("iso"))
                                else lang_row.get("iso")
                            ),
                        )
                        for _, lang_row in df_languages.iterrows()
                    ]

                    insert_sql = """
                        INSERT INTO languages (
                            id, user_id, iso
                        ) VALUES (%s, %s, %s)
                        """

                    chunk_size = 1000
                    with conn.cursor() as cursor:
                        for i in range(0, len(params), chunk_size):
                            chunk = params[i : i + chunk_size]
                            cursor.executemany(insert_sql, chunk)
                            summary["languages"] += len(chunk)
                else:
                    print("  No languages to insert")

                # Insert orders
                df_orders = orders.get("orders")
                if df_orders is not None and not df_orders.empty:
                    print(f"  Inserting {len(df_orders)} orders")
                    # orders table cleared above
                    params = [
                        (
                            order_row.name,
                            row.get("id"),
                            (
                                None
                                if pd.isna(order_row.get("totalItems"))
                                else order_row.get("totalItems")
                            ),
                            (
                                None
                                if pd.isna(order_row.get("total"))
                                else order_row.get("total")
                            ),
                            (
                                None
                                if pd.isna(order_row.get("currency_symbol"))
                                else order_row.get("currency_symbol")
                            ),
                            (
                                None
                                if pd.isna(order_row.get("createdAt"))
                                else order_row.get("createdAt")
                            ),
                            (
                                None
                                if pd.isna(order_row.get("customer_id"))
                                else order_row.get("customer_id")
                            ),
                            (
                                None
                                if pd.isna(order_row.get("language_id"))
                                else order_row.get("language_id")
                            ),
                        )
                        for _, order_row in df_orders.iterrows()
                    ]

                    insert_sql = """
                        INSERT INTO orders (
                            id, user_id, totalItems, total, currency_symbol,
                            createdAt, customer_id, language_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """

                    chunk_size = 1000
                    with conn.cursor() as cursor:
                        for i in range(0, len(params), chunk_size):
                            chunk = params[i : i + chunk_size]
                            cursor.executemany(insert_sql, chunk)
                            summary["orders"] += len(chunk)
                else:
                    print("  No orders to insert")

                # Insert product_categories
                df_product_categories = product_categories.get("product_categories")
                if (
                    df_product_categories is not None
                    and not df_product_categories.empty
                ):
                    print(
                        f"  Inserting {len(df_product_categories)} product_categories"
                    )
                    # product_categories table cleared above
                    params = [
                        (
                            prod_row.name,
                            row.get("id"),
                            (
                                None
                                if pd.isna(prod_row.get("path"))
                                else prod_row.get("path")
                            ),
                            (
                                None
                                if pd.isna(prod_row.get("title"))
                                else prod_row.get("title")
                            ),
                            (
                                None
                                if pd.isna(prod_row.get("createdAt"))
                                else prod_row.get("createdAt")
                            ),
                            (
                                None
                                if pd.isna(prod_row.get("updatedAt"))
                                else prod_row.get("updatedAt")
                            ),
                        )
                        for _, prod_row in df_product_categories.iterrows()
                    ]

                    insert_sql = """
                        INSERT INTO product_categories (
                            id, user_id, path, title, createdAt, updatedAt
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        """

                    chunk_size = 1000
                    with conn.cursor() as cursor:
                        for i in range(0, len(params), chunk_size):
                            chunk = params[i : i + chunk_size]
                            cursor.executemany(insert_sql, chunk)
                            summary["product_categories"] += len(chunk)
                else:
                    print("  No product_categories to insert")

                # Insert order_lines
                df_order_lines = orders.get("order_lines")
                if df_order_lines is not None and not df_order_lines.empty:
                    print(f"  Inserting {len(df_order_lines)} order lines")
                    # order_lines table cleared above
                    params = [
                        (
                            line_row.name,
                            row.get("id"),
                            (
                                None
                                if pd.isna(line_row.get("order_id"))
                                else line_row.get("order_id")
                            ),
                            (
                                None
                                if pd.isna(line_row.get("product_id"))
                                else line_row.get("product_id")
                            ),
                            (
                                None
                                if pd.isna(line_row.get("product_title"))
                                else line_row.get("product_title")
                            ),
                            (
                                None
                                if pd.isna(line_row.get("variant_title"))
                                else line_row.get("variant_title")
                            ),
                            (
                                None
                                if pd.isna(line_row.get("amount"))
                                else line_row.get("amount")
                            ),
                            (
                                None
                                if pd.isna(line_row.get("unit_revenue"))
                                else line_row.get("unit_revenue")
                            ),
                            (
                                None
                                if pd.isna(line_row.get("unit_cost"))
                                else line_row.get("unit_cost")
                            ),
                            (
                                None
                                if pd.isna(line_row.get("stock_status"))
                                else line_row.get("stock_status")
                            ),
                            (
                                None
                                if pd.isna(line_row.get("stock_amount"))
                                else line_row.get("stock_amount")
                            ),
                        )
                        for _, line_row in df_order_lines.iterrows()
                    ]

                    insert_sql = """
                        INSERT INTO order_lines (
                            order_line_id, user_id, order_id, product_id, product_title,
                            variant_title, amount, unit_revenue, unit_cost, stock_status, stock_amount
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """

                    chunk_size = 1000
                    with conn.cursor() as cursor:
                        for i in range(0, len(params), chunk_size):
                            chunk = params[i : i + chunk_size]
                            cursor.executemany(insert_sql, chunk)
                            summary["order_lines"] += len(chunk)
                else:
                    print("  No order lines to insert")

            elif row.get("platform_name") == "Dandomain Classic":

                # row = df_users.iloc[0]

                tenant = row.get("tenant")
                client_id = row.get("client_id")
                api_key = row.get("client_secret")
                print(f"Fetching token for {row.get('username')}")

                stmt = f"""
                            SELECT MAX(createdAt) FROM metlydk_main.orders
                            WHERE user_id = '{row.get('id')}';
                            """

                with conn.cursor() as cursor:
                    cursor.execute(stmt)
                    latest_order_date = cursor.fetchall()
                    print(f"  Latest order date in DB: {latest_order_date[0][0]}")

                orders = ClassicGetOrders(
                    api_key,
                    tenant,
                    max_pages=1200,
                    latest_order_date=latest_order_date[0][0],
                )

                # Delete existing rows for this user in child->parent order to avoid FK constraint errors
                order_line_ids = ",".join(
                    map(str, orders["order_lines"].index.tolist())
                )
                order_ids = ",".join(map(str, orders["orders"].index.tolist()))
                customer_ids = ",".join(map(str, orders["customers"].index.tolist()))
                language_ids = ",".join(map(str, orders["languages"].index.tolist()))

                try:
                    with conn.cursor() as cursor:
                        if len(order_line_ids) > 0:
                            cursor.execute(
                                f"DELETE FROM order_lines WHERE user_id = '{row.get('id')}' AND order_line_id IN ({order_line_ids});"
                            )
                        if len(order_ids) > 0:
                            cursor.execute(
                                f"DELETE FROM orders WHERE user_id = '{row.get('id')}' AND id IN ({order_ids});"
                            )
                        cursor.execute(
                            f"DELETE FROM product_categories WHERE user_id = '{row.get('id')}';"
                        )
                        cursor.execute(
                            f"DELETE FROM products WHERE user_id = '{row.get('id')}';"
                        )
                        if len(customer_ids) > 0:
                            cursor.execute(
                                f"DELETE FROM customers WHERE user_id = '{row.get('id')}' AND id IN ({customer_ids});"
                            )
                        if len(language_ids) > 0:
                            cursor.execute(
                                f"DELETE FROM languages WHERE user_id = '{row.get('id')}' AND id IN ({language_ids});"
                            )
                except Exception as e:
                    print(
                        f"  Warning: failed to delete existing rows for user id='{row.get('id')}': {e}"
                    )

                # Insert customers
                df_customers = orders.get("customers")

                if df_customers is not None and not df_customers.empty:
                    print(f"  Inserting {len(df_customers)} customers")

                    # customers table cleared above
                    # helper to convert pandas NA to SQL NULL
                    def _sql_val(v):
                        return None if pd.isna(v) else v

                    params = [
                        (
                            cust_row.name,
                            row.get("id"),
                            _sql_val(cust_row.get("billing_firstName")),
                            _sql_val(cust_row.get("billing_lastName")),
                            _sql_val(cust_row.get("billing_addressLine")),
                            _sql_val(cust_row.get("billing_city")),
                            _sql_val(cust_row.get("billing_zipCode")),
                            _sql_val(cust_row.get("billing_email")),
                            _sql_val(cust_row.get("extended_internal")),
                            _sql_val(cust_row.get("extended_external")),
                        )
                        for _, cust_row in df_customers.iterrows()
                    ]

                    insert_sql = """
                        INSERT INTO customers (
                            id, user_id, billing_firstName, billing_lastName,
                            billing_addressLine, billing_city, billing_zipCode, billing_email, extended_internal, extended_external
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """

                    chunk_size = 1000
                    with conn.cursor() as cursor:
                        for i in range(0, len(params), chunk_size):
                            chunk = params[i : i + chunk_size]
                            cursor.executemany(insert_sql, chunk)
                            summary["customers"] += len(chunk)
                else:
                    print("  No customers to insert")

                # Insert products
                df_products = ClassicGetProducts(api_key, tenant)

                if df_products is not None and not df_products.empty:
                    print(f"  Inserting {len(df_products)} products")

                    # helper to convert pandas NA to SQL NULL
                    def _sql_val(v):
                        return None if pd.isna(v) else v

                    params = [
                        (
                            _sql_val(product_row.get("productNumber")),
                            row.get("id"),
                            _sql_val(product_row.get("productName")),
                            _sql_val(product_row.get("subcategory_id")),
                            _sql_val(product_row.get("subcategory_name")),
                            _sql_val(product_row.get("maincategory_id")),
                            _sql_val(product_row.get("maincategory_name")),
                        )
                        for _, product_row in df_products.iterrows()
                    ]

                    insert_sql = """
                        INSERT INTO products (
                            id, user_id, product_name,
                            subcategory_id, subcategory_name, maincategory_id, maincategory_name
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """

                    chunk_size = 1000
                    with conn.cursor() as cursor:
                        for i in range(0, len(params), chunk_size):
                            chunk = params[i : i + chunk_size]
                            cursor.executemany(insert_sql, chunk)
                            summary["products"] += len(chunk)
                else:
                    print("  No products to insert")

                # Insert orders
                df_orders = orders.get("orders")

                if df_orders is not None and not df_orders.empty:
                    print(f"  Inserting {len(df_orders)} orders")
                    # orders table cleared above
                    params = [
                        (
                            order_row.name,
                            row.get("id"),
                            (
                                None
                                if pd.isna(order_row.get("totalItems"))
                                else order_row.get("totalItems")
                            ),
                            (
                                None
                                if pd.isna(order_row.get("total"))
                                else order_row.get("total")
                            ),
                            (
                                None
                                if pd.isna(order_row.get("currency_symbol"))
                                else order_row.get("currency_symbol")
                            ),
                            (
                                None
                                if pd.isna(order_row.get("createdAt"))
                                else order_row.get("createdAt")
                            ),
                            (
                                None
                                if pd.isna(order_row.get("customer_id"))
                                else order_row.get("customer_id")
                            ),
                            (
                                None
                                if pd.isna(order_row.get("language_id"))
                                else order_row.get("language_id")
                            ),
                            (
                                None
                                if pd.isna(order_row.get("referrer"))
                                else order_row.get("referrer")
                            ),
                        )
                        for _, order_row in df_orders.iterrows()
                    ]

                    insert_sql = """
                        INSERT INTO orders (
                            id, user_id, totalItems, total, currency_symbol,
                            createdAt, customer_id, language_id, referrer
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """

                    chunk_size = 1000
                    with conn.cursor() as cursor:
                        for i in range(0, len(params), chunk_size):
                            chunk = params[i : i + chunk_size]
                            cursor.executemany(insert_sql, chunk)
                            summary["orders"] += len(chunk)
                else:
                    print("  No orders to insert")

                # Insert order_lines
                df_order_lines = orders.get("order_lines")
                if df_order_lines is not None and not df_order_lines.empty:
                    print(f"  Inserting {len(df_order_lines)} order lines")
                    # order_lines table cleared above
                    params = [
                        (
                            line_row.name,
                            row.get("id"),
                            (
                                None
                                if pd.isna(line_row.get("order_id"))
                                else line_row.get("order_id")
                            ),
                            (
                                None
                                if pd.isna(line_row.get("product_id"))
                                else line_row.get("product_id")
                            ),
                            (
                                None
                                if pd.isna(line_row.get("product_title"))
                                else line_row.get("product_title")
                            ),
                            (
                                None
                                if pd.isna(line_row.get("variant_title"))
                                else line_row.get("variant_title")
                            ),
                            (
                                None
                                if pd.isna(line_row.get("amount"))
                                else line_row.get("amount")
                            ),
                            (
                                None
                                if pd.isna(line_row.get("unit_revenue"))
                                else line_row.get("unit_revenue")
                            ),
                            (
                                None
                                if pd.isna(line_row.get("unit_cost"))
                                else line_row.get("unit_cost")
                            ),
                            (
                                None
                                if pd.isna(line_row.get("stock_status"))
                                else line_row.get("stock_status")
                            ),
                            (
                                None
                                if pd.isna(line_row.get("stock_amount"))
                                else line_row.get("stock_amount")
                            ),
                        )
                        for _, line_row in df_order_lines.iterrows()
                    ]

                    insert_sql = """
                        INSERT INTO order_lines (
                            order_line_id, user_id, order_id, product_id, product_title,
                            variant_title, amount, unit_revenue, unit_cost, stock_status, stock_amount
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """

                    chunk_size = 1000
                    with conn.cursor() as cursor:
                        for i in range(0, len(params), chunk_size):
                            chunk = params[i : i + chunk_size]
                            cursor.executemany(insert_sql, chunk)
                            summary["order_lines"] += len(chunk)
                else:
                    print("  No order lines to insert")

            elif row.get("platform_name") == "demo":
                makeDummyData(conn, row.get("id"))

            elif row.get("platform_name") == "Shopify":

                tenant = row.get("tenant")
                access_token = row.get("client_secret")
                print(f"Fetching Shopify data for {row.get('username')}")

                if not tenant or not access_token:
                    print("  Missing Shopify tenant or access token, skipping user")
                    continue

                orders = ShopifyGetOrders(access_token, tenant)
                df_products = ShopifyGetProducts(access_token, tenant)

                try:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            f"DELETE FROM order_lines WHERE user_id = '{row.get('id')}';"
                        )
                        cursor.execute(
                            f"DELETE FROM orders WHERE user_id = '{row.get('id')}';"
                        )
                        cursor.execute(
                            f"DELETE FROM products WHERE user_id = '{row.get('id')}';"
                        )
                        cursor.execute(
                            f"DELETE FROM customers WHERE user_id = '{row.get('id')}';"
                        )
                        cursor.execute(
                            f"DELETE FROM languages WHERE user_id = '{row.get('id')}';"
                        )
                    conn.commit()
                except Exception as e:
                    print(
                        f"  Warning: failed to delete existing Shopify rows for user id='{row.get('id')}': {e}"
                    )

                df_customers = orders.get("customers")
                if df_customers is not None and not df_customers.empty:
                    print(f"  Inserting {len(df_customers)} customers")

                    def _sql_val(v):
                        return None if pd.isna(v) else v

                    params = [
                        (
                            cust_row.name,
                            row.get("id"),
                            _sql_val(cust_row.get("billing_firstName")),
                            _sql_val(cust_row.get("billing_lastName")),
                            _sql_val(cust_row.get("billing_addressLine")),
                            _sql_val(cust_row.get("billing_city")),
                            _sql_val(cust_row.get("billing_zipCode")),
                            _sql_val(cust_row.get("billing_email")),
                            _sql_val(cust_row.get("extended_internal")),
                            _sql_val(cust_row.get("extended_external")),
                        )
                        for _, cust_row in df_customers.iterrows()
                    ]

                    insert_sql = """
                        INSERT INTO customers (
                            id, user_id, billing_firstName, billing_lastName,
                            billing_addressLine, billing_city, billing_zipCode, billing_email, extended_internal, extended_external
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    with conn.cursor() as cursor:
                        cursor.executemany(insert_sql, params)
                        summary["customers"] += len(params)
                else:
                    print("  No Shopify customers to insert")

                if df_products is not None and not df_products.empty:
                    print(f"  Inserting {len(df_products)} products")

                    def _sql_val(v):
                        return None if pd.isna(v) else v

                    params = [
                        (
                            product_row.name,
                            row.get("id"),
                            _sql_val(product_row.get("product_name")),
                            _sql_val(product_row.get("subcategory_id")),
                            _sql_val(product_row.get("subcategory_name")),
                            _sql_val(product_row.get("maincategory_id")),
                            _sql_val(product_row.get("maincategory_name")),
                        )
                        for _, product_row in df_products.iterrows()
                    ]

                    insert_sql = """
                        INSERT INTO products (
                            id, user_id, product_name,
                            subcategory_id, subcategory_name, maincategory_id, maincategory_name
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """

                    with conn.cursor() as cursor:
                        cursor.executemany(insert_sql, params)
                        summary["products"] += len(params)
                else:
                    print("  No Shopify products to insert")

                df_orders = orders.get("orders")
                if df_orders is not None and not df_orders.empty:
                    print(f"  Inserting {len(df_orders)} orders")
                    params = [
                        (
                            order_row.name,
                            row.get("id"),
                            None if pd.isna(order_row.get("totalItems")) else order_row.get("totalItems"),
                            None if pd.isna(order_row.get("total")) else order_row.get("total"),
                            None if pd.isna(order_row.get("currency_symbol")) else order_row.get("currency_symbol"),
                            None if pd.isna(order_row.get("createdAt")) else order_row.get("createdAt"),
                            None if pd.isna(order_row.get("customer_id")) else order_row.get("customer_id"),
                            None if pd.isna(order_row.get("language_id")) else order_row.get("language_id"),
                            None if pd.isna(order_row.get("referrer")) else order_row.get("referrer"),
                        )
                        for _, order_row in df_orders.iterrows()
                    ]

                    insert_sql = """
                        INSERT INTO orders (
                            id, user_id, totalItems, total, currency_symbol,
                            createdAt, customer_id, language_id, referrer
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    with conn.cursor() as cursor:
                        cursor.executemany(insert_sql, params)
                        summary["orders"] += len(params)
                else:
                    print("  No Shopify orders to insert")

                df_order_lines = orders.get("order_lines")
                if df_order_lines is not None and not df_order_lines.empty:
                    print(f"  Inserting {len(df_order_lines)} order lines")
                    params = [
                        (
                            line_row.name,
                            row.get("id"),
                            None if pd.isna(line_row.get("order_id")) else line_row.get("order_id"),
                            None if pd.isna(line_row.get("product_id")) else line_row.get("product_id"),
                            None if pd.isna(line_row.get("product_title")) else line_row.get("product_title"),
                            None if pd.isna(line_row.get("variant_title")) else line_row.get("variant_title"),
                            None if pd.isna(line_row.get("amount")) else line_row.get("amount"),
                            None if pd.isna(line_row.get("unit_revenue")) else line_row.get("unit_revenue"),
                            None if pd.isna(line_row.get("unit_cost")) else line_row.get("unit_cost"),
                            None if pd.isna(line_row.get("stock_status")) else line_row.get("stock_status"),
                            None if pd.isna(line_row.get("stock_amount")) else line_row.get("stock_amount"),
                        )
                        for _, line_row in df_order_lines.iterrows()
                    ]

                    insert_sql = """
                        INSERT INTO order_lines (
                            order_line_id, user_id, order_id, product_id, product_title,
                            variant_title, amount, unit_revenue, unit_cost, stock_status, stock_amount
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    with conn.cursor() as cursor:
                        cursor.executemany(insert_sql, params)
                        summary["order_lines"] += len(params)
                else:
                    print("  No Shopify order lines to insert")

            # commit after processing each user
            print(f"Committing changes: {summary}")
            try:
                conn.commit()
            except Exception as e:
                print(f"  Warning: commit failed: {e}")
            print("Commit complete")

    except Exception as e:
        print(f"Write failed: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    populateDB(db_usr, db_pwd)
