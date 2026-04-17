import hashlib
import hmac
import random
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse, urlencode

import httpx
import pandas as pd


SHOPIFY_API_VERSION = "2025-10"

DANISH_FIRST_NAMES = [
    "Anders",
    "Anne",
    "Brian",
    "Camilla",
    "Claus",
    "Dorte",
    "Erik",
    "Frode",
    "Gitte",
    "Henrik",
    "Ida",
    "Jens",
    "Karen",
    "Lars",
    "Morten",
    "Niels",
    "Ole",
    "Pelle",
    "Rasmus",
    "Søren",
    "Thomas",
    "Ulla",
    "Vibeke",
    "William",
]

DANISH_LAST_NAMES = [
    "Andersen",
    "Berg",
    "Christensen",
    "Dahl",
    "Hansen",
    "Jensen",
    "Johansen",
    "Larsen",
    "Mortensen",
    "Nielsen",
    "Olsen",
    "Pedersen",
    "Rasmussen",
    "Sørensen",
    "Thomsen",
    "Winther",
]

DANISH_CITIES = [
    ("København", "1000-2990"),
    ("Aarhus", "8000-8200"),
    ("Odense", "5000-5290"),
    ("Aalborg", "9000-9210"),
    ("Esbjerg", "6700-6715"),
    ("Randers", "8900-8960"),
    ("Kolding", "6000-6090"),
    ("Horsens", "8700-8700"),
]

GOLF_PRODUCT_TEMPLATES = [
    ("Golfkølle - Driver", "Golfudstyr", "Driver", 1299.00),
    ("Golfkølle - Iron Set", "Golfudstyr", "Iron Set", 3499.00),
    ("Golfkølle - Putter", "Golfudstyr", "Putter", 599.00),
    ("Golfkølle - Wedge", "Golfudstyr", "Wedge", 449.00),
    ("Golftaske - Stand Bag", "Golfudstyr", "Tasker", 899.00),
    ("Golftaske - Cart Bag", "Golfudstyr", "Tasker", 1299.00),
    ("Golfbolde - Tour Pro (12 stk)", "Golfudstyr", "Bolde", 299.00),
    ("Golfbolde - Practice (50 stk)", "Golfudstyr", "Bolde", 149.00),
    ("Golfhandsker - Herre", "Golfbeklædning", "Tilbehør", 129.00),
    ("Golfhandsker - Dame", "Golfbeklædning", "Tilbehør", 129.00),
    ("Golfcap - Pro", "Golfbeklædning", "Hovedbeklædning", 199.00),
    ("Golfsko - Herre", "Golfbeklædning", "Sko", 899.00),
    ("Golfsko - Dame", "Golfbeklædning", "Sko", 899.00),
    ("Golftrøje - Poloshirt", "Golfbeklædning", "Trøjer", 349.00),
    ("Golfvest - Dame", "Golfbeklædning", "Vest", 599.00),
    ("Golfregnjakke", "Golfbeklædning", "Regntøj", 799.00),
    ("Golfhåndklæde", "Golftilbehør", "Tilbehør", 79.00),
    ("Golfscorekort-holder", "Golftilbehør", "Tilbehør", 149.00),
    ("Divot-værktøj", "Golftilbehør", "Tilbehør", 59.00),
    ("Tee-box (100 stk)", "Golftilbehør", "Tilbehør", 39.00),
]


def normalize_shop_domain(shop: str) -> str:
    raw_value = (shop or "").strip().lower()
    if not raw_value:
        raise ValueError("Invalid Shopify shop domain")

    normalized = raw_value
    if raw_value.startswith("http://") or raw_value.startswith("https://"):
        parsed = urlparse(raw_value)
        hostname = (parsed.hostname or "").lower()
        path_parts = [part for part in parsed.path.split("/") if part]

        if hostname == "admin.shopify.com":
            if len(path_parts) >= 2 and path_parts[0] == "store":
                normalized = path_parts[1]
            else:
                raise ValueError("Invalid Shopify admin URL")
        else:
            normalized = hostname

    normalized = normalized.strip("/")

    if not normalized.endswith(".myshopify.com"):
        normalized = f"{normalized}.myshopify.com"

    if not normalized.replace(".", "").replace("-", "").isalnum():
        raise ValueError("Invalid Shopify shop domain")

    if normalized.count(".") < 2:
        raise ValueError("Invalid Shopify shop domain")

    return normalized


def verify_shopify_hmac(params: dict[str, str], client_secret: str) -> bool:
    provided_hmac = params.get("hmac", "")
    if not provided_hmac:
        return False

    message = "&".join(
        f"{key}={value}"
        for key, value in sorted(params.items())
        if key not in {"hmac", "signature"}
    )
    digest = hmac.new(
        client_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(digest, provided_hmac)


def build_shopify_authorize_url(
    shop: str,
    client_id: str,
    scopes: str,
    redirect_uri: str,
    state: str,
) -> str:
    query = urlencode(
        {
            "client_id": client_id,
            "scope": scopes,
            "redirect_uri": redirect_uri,
            "state": state,
        }
    )
    return f"https://{shop}/admin/oauth/authorize?{query}"


def exchange_shopify_access_token(
    shop: str,
    client_id: str,
    client_secret: str,
    code: str,
) -> dict[str, Any]:
    response = httpx.post(
        f"https://{shop}/admin/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
        },
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


def _graphql_request(
    shop: str,
    access_token: str,
    query: str,
    variables: dict[str, Any],
) -> dict[str, Any]:
    response = httpx.post(
        f"https://{shop}/admin/api/{SHOPIFY_API_VERSION}/graphql.json",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Shopify-Access-Token": access_token,
        },
        json={"query": query, "variables": variables},
        timeout=60.0,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(f"Shopify GraphQL error: {payload['errors']}")
    return payload.get("data", {})


def _to_shopify_search_timestamp(value: datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        parsed = value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _updated_since_query(field_name: str, value: datetime | str | None) -> str | None:
    normalized = _to_shopify_search_timestamp(value)
    if not normalized:
        return None
    return f"{field_name}:>={normalized}"


def get_orders(
    access_token: str,
    shop: str,
    page_size: int = 50,
    updated_since: datetime | str | None = None,
) -> dict[str, pd.DataFrame]:
    query = """
    query Orders($first: Int!, $after: String, $query: String) {
      orders(first: $first, after: $after, sortKey: UPDATED_AT, reverse: true, query: $query) {
        pageInfo {
          hasNextPage
          endCursor
        }
        edges {
          node {
            id
            createdAt
            updatedAt
            currentTotalPriceSet {
              shopMoney {
                amount
                currencyCode
              }
            }
            customer {
              id
            }
            lineItems(first: 100) {
              edges {
                node {
                  id
                  name
                  quantity
                  discountedUnitPriceAfterAllDiscountsSet {
                    shopMoney {
                      amount
                    }
                  }
                  originalUnitPriceSet {
                    shopMoney {
                      amount
                    }
                  }
                  product {
                    id
                    title
                    productType
                    vendor
                  }
                  variant {
                    title
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    orders_rows: list[dict[str, Any]] = []
    customers_map: dict[str, dict[str, Any]] = {}
    order_lines_rows: list[dict[str, Any]] = []
    cursor: str | None = None

    while True:
        search_query = _updated_since_query("updated_at", updated_since)
        payload = _graphql_request(
            shop,
            access_token,
            query,
            {"first": page_size, "after": cursor, "query": search_query},
        )
        orders = payload.get("orders", {})

        for edge in orders.get("edges", []):
            node = edge.get("node", {})
            order_id = node.get("id")
            customer = node.get("customer") or {}
            customer_id = customer.get("id")
            line_edges = (node.get("lineItems") or {}).get("edges", [])

            if customer_id:
                customers_map[customer_id] = {
                    "customer_id": customer_id,
                    "billing_firstName": None,
                    "billing_lastName": None,
                    "billing_addressLine": None,
                    "billing_city": None,
                    "billing_zipCode": None,
                    "billing_email": None,
                    "extended_internal": None,
                    "extended_external": None,
                }

            money = (node.get("currentTotalPriceSet") or {}).get("shopMoney") or {}
            total_items = sum(
                (line.get("node") or {}).get("quantity", 0) for line in line_edges
            )
            orders_rows.append(
                {
                    "order_id": order_id,
                    "totalItems": total_items,
                    "total": money.get("amount"),
                    "currency_symbol": money.get("currencyCode"),
                    "createdAt": node.get("createdAt"),
                    "updatedAt": node.get("updatedAt"),
                    "customer_id": customer_id,
                    "language_id": None,
                    "referrer": "shopify",
                }
            )

            for line_edge in line_edges:
                line_item = line_edge.get("node", {})
                discounted_money = (
                    line_item.get("discountedUnitPriceAfterAllDiscountsSet") or {}
                ).get("shopMoney") or {}
                original_money = (line_item.get("originalUnitPriceSet") or {}).get(
                    "shopMoney"
                ) or {}
                product = line_item.get("product") or {}
                variant = line_item.get("variant") or {}

                order_lines_rows.append(
                    {
                        "order_line_id": line_item.get("id"),
                        "order_id": order_id,
                        "product_id": product.get("id"),
                        "product_title": line_item.get("name") or product.get("title"),
                        "variant_title": variant.get("title"),
                        "amount": line_item.get("quantity"),
                        "unit_revenue": discounted_money.get("amount")
                        or original_money.get("amount"),
                        "unit_cost": None,
                        "stock_status": None,
                        "stock_amount": None,
                    }
                )

        page_info = orders.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")

    orders_df = pd.DataFrame(orders_rows)
    customers_df = pd.DataFrame(list(customers_map.values()))
    order_lines_df = pd.DataFrame(order_lines_rows)
    languages_df = pd.DataFrame(columns=["language_id", "iso"])

    if not orders_df.empty and "order_id" in orders_df.columns:
        orders_df = orders_df.set_index("order_id")
    if not customers_df.empty and "customer_id" in customers_df.columns:
        customers_df = customers_df.set_index("customer_id")
    if not order_lines_df.empty and "order_line_id" in order_lines_df.columns:
        order_lines_df = order_lines_df.set_index("order_line_id")
    if not languages_df.empty and "language_id" in languages_df.columns:
        languages_df = languages_df.set_index("language_id")

    return {
        "orders": orders_df,
        "customers": customers_df,
        "order_lines": order_lines_df,
        "languages": languages_df,
    }


def _products_dataframe_from_rows(rows: list[dict[str, Any]]) -> pd.DataFrame:
    products_df = pd.DataFrame(rows)
    if not products_df.empty and "id" in products_df.columns:
        products_df = products_df.drop_duplicates(subset=["id"], keep="first")
        products_df = products_df.set_index("id")
    return products_df


def get_products(
    access_token: str,
    shop: str,
    page_size: int = 100,
    updated_since: datetime | str | None = None,
    product_ids: list[str] | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    if product_ids:
        for i in range(0, len(product_ids), page_size):
            chunk = product_ids[i : i + page_size]
            payload = _graphql_request(
                shop,
                access_token,
                """
                query ProductsByIds($ids: [ID!]!) {
                  nodes(ids: $ids) {
                    ... on Product {
                      id
                      title
                      productType
                      vendor
                      updatedAt
                    }
                  }
                }
                """,
                {"ids": chunk},
            )
            for node in payload.get("nodes", []):
                if not node:
                    continue
                rows.append(
                    {
                        "id": node.get("id"),
                        "product_name": node.get("title"),
                        "subcategory_id": node.get("productType") or "shopify-default",
                        "subcategory_name": node.get("productType")
                        or "Shopify products",
                        "maincategory_id": node.get("vendor") or "shopify",
                        "maincategory_name": node.get("vendor") or "Shopify",
                        "updatedAt": node.get("updatedAt"),
                    }
                )
    else:
        query = """
        query Products($first: Int!, $after: String, $query: String) {
          products(first: $first, after: $after, sortKey: UPDATED_AT, reverse: true, query: $query) {
            pageInfo {
              hasNextPage
              endCursor
            }
            edges {
              node {
                id
                title
                productType
                vendor
                updatedAt
              }
            }
          }
        }
        """

        cursor: str | None = None

        while True:
            search_query = _updated_since_query("updated_at", updated_since)
            payload = _graphql_request(
                shop,
                access_token,
                query,
                {"first": page_size, "after": cursor, "query": search_query},
            )
            products = payload.get("products", {})

            for edge in products.get("edges", []):
                node = edge.get("node", {})
                rows.append(
                    {
                        "id": node.get("id"),
                        "product_name": node.get("title"),
                        "subcategory_id": node.get("productType") or "shopify-default",
                        "subcategory_name": node.get("productType")
                        or "Shopify products",
                        "maincategory_id": node.get("vendor") or "shopify",
                        "maincategory_name": node.get("vendor") or "Shopify",
                        "updatedAt": node.get("updatedAt"),
                    }
                )

            page_info = products.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info.get("endCursor")

    return _products_dataframe_from_rows(rows)


def _random_danish_name():
    return f"{random.choice(DANISH_FIRST_NAMES)} {random.choice(DANISH_LAST_NAMES)}"


def _random_danish_address():
    city, zip_range = random.choice(DANISH_CITIES)
    zip_start, zip_end = zip_range.split("-")
    zip_code = random.randint(int(zip_start), int(zip_end))
    street_num = random.randint(1, 200)
    return f"Golfvej {street_num}", city, str(zip_code)


def create_product(
    access_token: str,
    shop: str,
    title: str,
    product_type: str,
    vendor: str,
    price: float,
) -> dict[str, Any]:
    response = httpx.post(
        f"https://{shop}/admin/api/{SHOPIFY_API_VERSION}/products.json",
        headers={
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": access_token,
        },
        json={
            "product": {
                "title": title,
                "product_type": product_type,
                "vendor": vendor,
                "variants": [
                    {
                        "price": str(price),
                        "inventory_policy": "deny",
                        "inventory_quantity": 100,
                    }
                ],
            }
        },
        timeout=60.0,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("product", {})


def create_products(
    access_token: str,
    shop: str,
    product_count: int = 20,
) -> list[dict[str, Any]]:
    created = []
    for i in range(product_count):
        template = GOLF_PRODUCT_TEMPLATES[i % len(GOLF_PRODUCT_TEMPLATES)]
        title, vendor, product_type, price = template
        if i >= len(GOLF_PRODUCT_TEMPLATES):
            title = f"{title} {i // len(GOLF_PRODUCT_TEMPLATES) + 1}"

        product = create_product(access_token, shop, title, product_type, vendor, price)
        created.append(product)
        print(f"  Created product: {title}")
        import time

        time.sleep(0.5)

    return created


def create_orders(
    access_token: str,
    shop: str,
    products: list[dict[str, Any]],
    order_count: int = 10,
) -> list[dict[str, Any]]:
    created = []
    for i in range(order_count):
        selected = random.sample(products, min(random.randint(1, 3), len(products)))
        line_items = []
        for p in selected:
            pid = p.get("id", "")
            if pid:
                numeric_id = pid.replace("gid://shopify/Product/", "")
                price = random.uniform(100, 2000)
                line_items.append(
                    {
                        "product_id": numeric_id,
                        "quantity": random.randint(1, 3),
                        "price": f"{price:.2f}",
                    }
                )

        if not line_items:
            continue

        email = f"kunde{i + 1}@golfmail.dk"

        # Retry with backoff on rate limit
        max_retries = 3
        for attempt in range(max_retries):
            response = httpx.post(
                f"https://{shop}/admin/api/{SHOPIFY_API_VERSION}/orders.json",
                headers={
                    "Content-Type": "application/json",
                    "X-Shopify-Access-Token": access_token,
                },
                json={
                    "order": {
                        "line_items": line_items,
                        "email": email,
                        "financial_status": "paid",
                    }
                },
                timeout=60.0,
            )
            if response.status_code == 429:
                wait_time = (attempt + 1) * 2  # 2, 4, 6 seconds
                print(f"  Rate limited, waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            break

        if response.status_code != 200:
            print(f"  Error: {response.status_code} - {response.text[:300]}")
        response.raise_for_status()
        order = response.json().get("order", {})
        created.append(order)
        print(f"  Created order: {order.get('name', 'Order')}")

        # Delay between orders to avoid rate limits
        time.sleep(1)

    return created


def create_draft_order(
    access_token: str,
    shop: str,
    product_ids: list[str],
    customer_email: str | None = None,
) -> dict[str, Any]:
    mutation = """
    mutation DraftOrderCreate($input: DraftOrderInput!) {
        draftOrderCreate(input: $input) {
            draftOrder {
                id
                name
                totalPrice
            }
            userErrors {
                field
                message
            }
        }
    }
    """
    line_items = [
        {"quantity": random.randint(1, 3), "variantId": pid}
        for pid in product_ids[: random.randint(1, min(5, len(product_ids)))]
    ]

    input_data = {
        "lineItems": line_items,
        "useCustomerDefaultAddress": customer_email is None,
    }

    if customer_email:
        input_data["email"] = customer_email

    payload = _graphql_request(shop, access_token, mutation, {"input": input_data})

    result = payload.get("draftOrderCreate", {})
    if result.get("userErrors"):
        errors = result["userErrors"]
        raise RuntimeError(f"Shopify draft order create error: {errors}")

    return result.get("draftOrder", {})


def complete_draft_order(
    access_token: str,
    shop: str,
    draft_order_id: str,
) -> dict[str, Any]:
    mutation = """
    mutation DraftOrderComplete($input: DraftOrderCompleteInput!) {
        draftOrderComplete(input: $input) {
            order {
                id
                name
                totalPriceSet {
                    shopMoney {
                        amount
                    }
                }
            }
            userErrors {
                field
                message
            }
        }
    }
    """
    payload = _graphql_request(
        shop, access_token, mutation, {"input": {"draftOrderId": draft_order_id}}
    )

    result = payload.get("draftOrderComplete", {})
    if result.get("userErrors"):
        errors = result["userErrors"]
        raise RuntimeError(f"Shopify draft order complete error: {errors}")

    return result.get("order", {})


def create_orders(
    access_token: str,
    shop: str,
    products: list[dict[str, Any]],
    order_count: int = 10,
) -> list[dict[str, Any]]:
    created = []
    for i in range(order_count):
        selected = random.sample(products, min(random.randint(1, 3), len(products)))

        if not selected:
            continue

        email = f"kunde{i + 1}@golfmail.dk"

        line_items = []
        for p in selected:
            price = round(random.uniform(100, 2000), 2)
            line_items.append(
                {
                    "title": p.get("product_name", "Product"),
                    "quantity": random.randint(1, 3),
                    "price": str(price),
                }
            )

        try:
            response = httpx.post(
                f"https://{shop}/admin/api/2024-10/orders.json",
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
                                "amount": str(
                                    sum(
                                        float(l["price"]) * l["quantity"]
                                        for l in line_items
                                    )
                                ),
                            }
                        ],
                    }
                },
                timeout=60.0,
            )

            if response.status_code != 201:
                print(f"  Error: {response.status_code} - {response.text[:200]}")
                continue

            order = response.json().get("order", {})
            created.append(order)
            print(f"  Created order: {order.get('name', 'Order')}")
        except Exception as e:
            print(f"  Error: {e}")
            continue

        import time

        time.sleep(0.5)

    return created

    query = """
    query Products($first: Int!, $after: String, $query: String) {
      products(first: $first, after: $after, sortKey: UPDATED_AT, reverse: true, query: $query) {
        pageInfo {
          hasNextPage
          endCursor
        }
        edges {
          node {
            id
            title
            productType
            vendor
            updatedAt
          }
        }
      }
    }
    """

    rows: list[dict[str, Any]] = []
    cursor: str | None = None

    while True:
        search_query = _updated_since_query("updated_at", updated_since)
        payload = _graphql_request(
            shop,
            access_token,
            query,
            {"first": page_size, "after": cursor, "query": search_query},
        )
        products = payload.get("products", {})

        for edge in products.get("edges", []):
            node = edge.get("node", {})
            rows.append(
                {
                    "id": node.get("id"),
                    "product_name": node.get("title"),
                    "subcategory_id": node.get("productType") or "shopify-default",
                    "subcategory_name": node.get("productType") or "Shopify products",
                    "maincategory_id": node.get("vendor") or "shopify",
                    "maincategory_name": node.get("vendor") or "Shopify",
                    "updatedAt": node.get("updatedAt"),
                }
            )

        page_info = products.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")

    return _products_dataframe_from_rows(rows)
