from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
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
SHOPIFY_DELTA_LOOKBACK_DAYS = int(os.getenv("SHOPIFY_DELTA_LOOKBACK_DAYS", "7"))


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
                "read_timeout": 120,
                "write_timeout": 120,
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
                read_timeout=120,
                write_timeout=120,
                autocommit=False,
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


def _sql_val(v):
    return None if pd.isna(v) else v


def _chunked(values, chunk_size: int = 1000):
    for i in range(0, len(values), chunk_size):
        yield values[i : i + chunk_size]


def _chunked_delete(
    cursor, conn, table: str, user_id: str, chunk_size: int = 1000, max_retries: int = 3
):
    """Delete rows in chunks to avoid MySQL timeout on large tables."""
    import time

    for attempt in range(max_retries):
        try:
            while True:
                cursor.execute(
                    f"DELETE FROM {table} WHERE user_id = '{user_id}' LIMIT {chunk_size}"
                )
                conn.commit()
                if cursor.rowcount < chunk_size:
                    break
            break
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                print(f"    Delete failed for {table}: {e}")


def _get_latest_timestamp(conn, table_name: str, column_name: str, user_id):
    query = f"SELECT MAX({column_name}) FROM {table_name} WHERE user_id = %s"
    with conn.cursor() as cursor:
        cursor.execute(query, (str(user_id),))
        result = cursor.fetchone()
    return result[0] if result else None


def _delta_window_start(
    latest_timestamp, lookback_days: int = SHOPIFY_DELTA_LOOKBACK_DAYS
):
    if latest_timestamp is None:
        return None
    if isinstance(latest_timestamp, str):
        latest_timestamp = datetime.fromisoformat(
            latest_timestamp.replace("Z", "+00:00")
        )
    if latest_timestamp.tzinfo is None:
        latest_timestamp = latest_timestamp.replace(tzinfo=timezone.utc)
    return latest_timestamp - timedelta(days=lookback_days)


def _delete_rows_for_ids(conn, table_name: str, id_column: str, user_id, record_ids):
    ids = [str(record_id) for record_id in record_ids if record_id]
    if not ids:
        return
    for chunk in _chunked(ids):
        placeholders = ",".join(["%s"] * len(chunk))
        query = (
            f"DELETE FROM {table_name} "
            f"WHERE user_id = %s AND {id_column} IN ({placeholders})"
        )
        with conn.cursor() as cursor:
            cursor.execute(query, [str(user_id), *chunk])
        conn.commit()


def _combine_product_frames(*frames: pd.DataFrame) -> pd.DataFrame:
    non_empty_frames = [
        frame.reset_index() for frame in frames if frame is not None and not frame.empty
    ]
    if not non_empty_frames:
        return pd.DataFrame()
    combined = pd.concat(non_empty_frames, ignore_index=True)
    combined = combined.drop_duplicates(subset=["id"], keep="first")
    return combined.set_index("id")


def _validate_shopify_payload(
    orders: dict[str, pd.DataFrame], df_products: pd.DataFrame
):
    df_orders = orders.get("orders")
    df_customers = orders.get("customers")
    df_order_lines = orders.get("order_lines")

    if df_orders is not None and not df_orders.empty:
        customer_index = (
            set()
            if df_customers is None or df_customers.empty
            else {str(index) for index in df_customers.index}
        )
        missing_customer_ids = {
            str(customer_id)
            for customer_id in df_orders["customer_id"].dropna().astype(str)
            if customer_id not in customer_index
        }
        if missing_customer_ids:
            raise ValueError(
                "Shopify payload validation failed: orders reference missing customers "
                f"({len(missing_customer_ids)} ids)"
            )

    if df_order_lines is not None and not df_order_lines.empty:
        order_index = (
            set()
            if df_orders is None or df_orders.empty
            else {str(index) for index in df_orders.index}
        )
        missing_order_ids = {
            str(order_id)
            for order_id in df_order_lines["order_id"].dropna().astype(str)
            if order_id not in order_index
        }
        if missing_order_ids:
            raise ValueError(
                "Shopify payload validation failed: order lines reference missing orders "
                f"({len(missing_order_ids)} ids)"
            )

    if df_order_lines is not None and not df_order_lines.empty:
        product_index = (
            set()
            if df_products is None or df_products.empty
            else {str(index) for index in df_products.index}
        )
        missing_product_ids = {
            str(product_id)
            for product_id in df_order_lines["product_id"].dropna().astype(str)
            if product_id not in product_index
        }
        if missing_product_ids:
            logger.warning(
                "Shopify payload contains %d product ids not returned by product sync",
                len(missing_product_ids),
            )


def populateDB(db_usr, db_pwd, user_ids=None, raise_on_error: bool = False):

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

    if user_ids:
        user_ids_set = {str(user_id) for user_id in user_ids}
        df_users = df_users[df_users["id"].astype(str).isin(user_ids_set)].copy()
        if df_users.empty:
            print("No matching users fetched from the remote database. Nothing to do.")
            return

    try:
        # Summary for inserted rows. Cursors are created as needed using context managers
        # to avoid holding many open cursors at once.
        print("[DEBUG] About to iterate over users")
        print(f"[DEBUG] Number of users: {len(df_users)}")

        skip_dandomain_modern = (
            os.getenv("SKIP_DANDOMAIN_MODERN", "false").lower() == "true"
        )
        print(f"[DEBUG] SKIP_DANDOMAIN_MODERN = {skip_dandomain_modern}")

        for idx, row in df_users.iterrows():
            print(
                f"[DEBUG] Processing user {idx}: {row.get('username')} ({row.get('platform_name')})"
            )
            if row.get("platform_name") == "Dandomain Modern":
                if skip_dandomain_modern:
                    print(
                        f"Skipping Dandomain Modern for {row.get('username')} (SKIP_DANDOMAIN_MODERN=true)"
                    )
                    continue
                tenant = row.get("tenant")
                client_id = row.get("client_id")
                client_secret = row.get("client_secret")
                print(f"Fetching token for {row.get('username')}")
                token = getDandomainToken(tenant, client_id, client_secret)
                orders = ModernGetOrders(token, tenant)
                product_categories = getProductCategories(token, tenant)

                # Delete existing rows for this user in child->parent order to avoid FK constraint errors
                # Ping to check if connection is still alive, reconnect if not
                try:
                    conn.ping(True)
                except Exception:
                    conn, df_users = connectDB(db_usr, db_pwd)

                # Use chunked deletes with LIMIT to avoid timeouts on large tables
                try:
                    with conn.cursor() as cursor:
                        _chunked_delete(cursor, conn, "order_lines", row.get("id"))
                        _chunked_delete(cursor, conn, "orders", row.get("id"))
                        _chunked_delete(
                            cursor, conn, "product_categories", row.get("id")
                        )
                        _chunked_delete(cursor, conn, "customers", row.get("id"))
                        _chunked_delete(cursor, conn, "languages", row.get("id"))
                except Exception as e:
                    print(
                        f"  Warning: failed to delete existing rows for user id='{row.get('id')}': {e}"
                    )

                # Insert customers
                df_customers = orders.get("customers")
                if df_customers is not None and not df_customers.empty:
                    print(f"  Inserting {len(df_customers)} customers")

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
                            conn.commit()
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
                            conn.commit()
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
                            conn.commit()
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
                            conn.commit()
                            summary["product_categories"] += len(chunk)
                else:
                    print("  No product_categories to insert")

                print(
                    f"  [DEBUG] About to process order_lines for user {row.get('id')}"
                )
                # Insert order_lines
                df_order_lines = orders.get("order_lines")
                if df_order_lines is not None and not df_order_lines.empty:
                    print(f"  Inserting {len(df_order_lines)} order lines")
                    print(
                        f"  [DEBUG] Order lines DataFrame shape: {df_order_lines.shape}"
                    )
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
                    print(f"  [DEBUG] Inserting order_lines in chunks of {chunk_size}")
                    with conn.cursor() as cursor:
                        for i in range(0, len(params), chunk_size):
                            print(
                                f"  [DEBUG] Inserting chunk {i // chunk_size + 1}: {len(chunk)} rows"
                            )
                            cursor.executemany(insert_sql, chunk)
                            conn.commit()
                            summary["order_lines"] += len(chunk)
                    print(
                        f"  [DEBUG] Finished inserting order_lines for user {row.get('id')}"
                    )
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
                            WHERE user_id = '{row.get("id")}';
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
                            conn.commit()
                        if len(order_ids) > 0:
                            cursor.execute(
                                f"DELETE FROM orders WHERE user_id = '{row.get('id')}' AND id IN ({order_ids});"
                            )
                            conn.commit()
                        cursor.execute(
                            f"DELETE FROM product_categories WHERE user_id = '{row.get('id')}';"
                        )
                        conn.commit()
                        cursor.execute(
                            f"DELETE FROM products WHERE user_id = '{row.get('id')}';"
                        )
                        conn.commit()
                        if len(customer_ids) > 0:
                            cursor.execute(
                                f"DELETE FROM customers WHERE user_id = '{row.get('id')}' AND id IN ({customer_ids});"
                            )
                            conn.commit()
                        if len(language_ids) > 0:
                            cursor.execute(
                                f"DELETE FROM languages WHERE user_id = '{row.get('id')}' AND id IN ({language_ids});"
                            )
                            conn.commit()
                except Exception as e:
                    print(
                        f"  Warning: failed to delete existing rows for user id='{row.get('id')}': {e}"
                    )

                # Insert customers
                df_customers = orders.get("customers")

                if df_customers is not None and not df_customers.empty:
                    print(f"  Inserting {len(df_customers)} customers")

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
                            conn.commit()
                            summary["customers"] += len(chunk)
                else:
                    print("  No customers to insert")

                # Insert products
                df_products = ClassicGetProducts(api_key, tenant)

                if df_products is not None and not df_products.empty:
                    print(f"  Inserting {len(df_products)} products")

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
                            conn.commit()
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
                            conn.commit()
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
                            conn.commit()
                            summary["order_lines"] += len(chunk)
                else:
                    print("  No order lines to insert")

            elif row.get("platform_name") == "demo":
                makeDummyData(conn, row.get("id"))

            elif row.get("platform_name") == "Shopify":
                tenant = row.get("tenant")
                access_token = row.get("client_secret")
                user_id = row.get("id")
                print(f"Fetching Shopify data for {row.get('username')}")

                if not tenant or not access_token:
                    missing_fields = []
                    if not tenant:
                        missing_fields.append("tenant")
                    if not access_token:
                        missing_fields.append("access_token")
                    print(
                        "  Missing Shopify credentials in users row"
                        f" ({', '.join(missing_fields)}), skipping user"
                    )
                    continue

                latest_order_created_at = _get_latest_timestamp(
                    conn, "orders", "createdAt", user_id
                )
                latest_product_sync_at = _get_latest_timestamp(
                    conn, "products", "created", user_id
                )
                order_delta_since = _delta_window_start(latest_order_created_at)
                product_delta_since = _delta_window_start(latest_product_sync_at)

                print(
                    "  Shopify delta window:"
                    f" orders since {order_delta_since or 'beginning'},"
                    f" products since {product_delta_since or 'beginning'}"
                )

                orders = ShopifyGetOrders(
                    access_token,
                    tenant,
                    updated_since=order_delta_since,
                )
                df_orders = orders.get("orders")
                df_order_lines = orders.get("order_lines")

                order_product_ids = []
                if df_order_lines is not None and not df_order_lines.empty:
                    order_product_ids = (
                        df_order_lines["product_id"]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )

                df_products = _combine_product_frames(
                    ShopifyGetProducts(
                        access_token,
                        tenant,
                        updated_since=product_delta_since,
                    ),
                    ShopifyGetProducts(
                        access_token,
                        tenant,
                        product_ids=order_product_ids,
                    )
                    if order_product_ids
                    else pd.DataFrame(),
                )

                _validate_shopify_payload(orders, df_products)

                try:
                    _delete_rows_for_ids(
                        conn,
                        "order_lines",
                        "order_line_id",
                        user_id,
                        []
                        if df_order_lines is None or df_order_lines.empty
                        else df_order_lines.index.tolist(),
                    )
                    _delete_rows_for_ids(
                        conn,
                        "orders",
                        "id",
                        user_id,
                        []
                        if df_orders is None or df_orders.empty
                        else df_orders.index.tolist(),
                    )
                    _delete_rows_for_ids(
                        conn,
                        "products",
                        "id",
                        user_id,
                        []
                        if df_products is None or df_products.empty
                        else df_products.index.tolist(),
                    )
                    _delete_rows_for_ids(
                        conn,
                        "customers",
                        "id",
                        user_id,
                        []
                        if orders.get("customers") is None
                        or orders.get("customers").empty
                        else orders.get("customers").index.tolist(),
                    )
                    _delete_rows_for_ids(
                        conn,
                        "languages",
                        "id",
                        user_id,
                        []
                        if orders.get("languages") is None
                        or orders.get("languages").empty
                        else orders.get("languages").index.tolist(),
                    )
                except Exception as e:
                    print(
                        f"  Warning: failed to delete existing Shopify rows for user id='{user_id}': {e}"
                    )

                df_customers = orders.get("customers")
                if df_customers is not None and not df_customers.empty:
                    print(f"  Inserting {len(df_customers)} customers")

                    params = [
                        (
                            cust_row.name,
                            user_id,
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
                        for chunk in _chunked(params):
                            cursor.executemany(insert_sql, chunk)
                            conn.commit()
                            summary["customers"] += len(chunk)
                else:
                    print("  No Shopify customers to insert")

                if df_products is not None and not df_products.empty:
                    print(f"  Inserting {len(df_products)} products")

                    params = [
                        (
                            product_row.name,
                            user_id,
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
                        for chunk in _chunked(params):
                            cursor.executemany(insert_sql, chunk)
                            conn.commit()
                            summary["products"] += len(chunk)
                else:
                    print("  No Shopify products to insert")

                if df_orders is not None and not df_orders.empty:
                    print(f"  Inserting {len(df_orders)} orders")
                    params = [
                        (
                            order_row.name,
                            user_id,
                            _sql_val(order_row.get("totalItems")),
                            _sql_val(order_row.get("total")),
                            _sql_val(order_row.get("currency_symbol")),
                            _sql_val(order_row.get("createdAt")),
                            _sql_val(order_row.get("customer_id")),
                            _sql_val(order_row.get("language_id")),
                            _sql_val(order_row.get("referrer")),
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
                        for chunk in _chunked(params):
                            cursor.executemany(insert_sql, chunk)
                            conn.commit()
                            summary["orders"] += len(chunk)
                else:
                    print("  No Shopify orders to insert")

                if df_order_lines is not None and not df_order_lines.empty:
                    print(f"  Inserting {len(df_order_lines)} order lines")
                    params = [
                        (
                            line_row.name,
                            user_id,
                            _sql_val(line_row.get("order_id")),
                            _sql_val(line_row.get("product_id")),
                            _sql_val(line_row.get("product_title")),
                            _sql_val(line_row.get("variant_title")),
                            _sql_val(line_row.get("amount")),
                            _sql_val(line_row.get("unit_revenue")),
                            _sql_val(line_row.get("unit_cost")),
                            _sql_val(line_row.get("stock_status")),
                            _sql_val(line_row.get("stock_amount")),
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
                        for chunk in _chunked(params):
                            cursor.executemany(insert_sql, chunk)
                            conn.commit()
                            summary["order_lines"] += len(chunk)
                else:
                    print("  No Shopify order lines to insert")

            # commit after processing each user
            print(f"Committing changes: {summary}")
            print(f"  [DEBUG] About to commit for user {row.get('id')}")
            try:
                conn.commit()
                print(f"  [DEBUG] Commit succeeded for user {row.get('id')}")
            except Exception as e:
                print(f"  Warning: commit failed: {e}")
            print("Commit complete")

    except Exception as e:
        print(f"Write failed: {e}")
        if raise_on_error:
            raise
    finally:
        try:
            conn.close()
        except Exception:
            pass

    print("[DEBUG] populateDB function completed successfully")


if __name__ == "__main__":
    print("[DEBUG] Starting populateDB from main")
    populateDB(db_usr, db_pwd)
    print("[DEBUG] populateDB called from __main__ finished")
