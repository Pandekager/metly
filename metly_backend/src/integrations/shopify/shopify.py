import hashlib
import hmac
from typing import Any
from urllib.parse import urlparse, urlencode

import httpx
import pandas as pd


SHOPIFY_API_VERSION = "2025-10"


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


def get_orders(access_token: str, shop: str, page_size: int = 50) -> dict[str, pd.DataFrame]:
    query = """
    query Orders($first: Int!, $after: String) {
      orders(first: $first, after: $after, sortKey: CREATED_AT, reverse: true) {
        pageInfo {
          hasNextPage
          endCursor
        }
        edges {
          node {
            id
            createdAt
            currentTotalPriceSet {
              shopMoney {
                amount
                currencyCode
              }
            }
            customer {
              id
              firstName
              lastName
              email
              defaultAddress {
                address1
                city
                zip
              }
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
        payload = _graphql_request(
            shop,
            access_token,
            query,
            {"first": page_size, "after": cursor},
        )
        orders = payload.get("orders", {})

        for edge in orders.get("edges", []):
            node = edge.get("node", {})
            order_id = node.get("id")
            customer = node.get("customer") or {}
            customer_id = customer.get("id")
            line_edges = (node.get("lineItems") or {}).get("edges", [])

            if customer_id:
                address = customer.get("defaultAddress") or {}
                customers_map[customer_id] = {
                    "customer_id": customer_id,
                    "billing_firstName": customer.get("firstName"),
                    "billing_lastName": customer.get("lastName"),
                    "billing_addressLine": address.get("address1"),
                    "billing_city": address.get("city"),
                    "billing_zipCode": address.get("zip"),
                    "billing_email": customer.get("email"),
                    "extended_internal": None,
                    "extended_external": None,
                }

            money = ((node.get("currentTotalPriceSet") or {}).get("shopMoney") or {})
            total_items = sum((line.get("node") or {}).get("quantity", 0) for line in line_edges)
            orders_rows.append(
                {
                    "order_id": order_id,
                    "totalItems": total_items,
                    "total": money.get("amount"),
                    "currency_symbol": money.get("currencyCode"),
                    "createdAt": node.get("createdAt"),
                    "customer_id": customer_id,
                    "language_id": None,
                    "referrer": "shopify",
                }
            )

            for line_edge in line_edges:
                line_item = line_edge.get("node", {})
                discounted_money = (
                    ((line_item.get("discountedUnitPriceAfterAllDiscountsSet") or {}).get("shopMoney") or {})
                )
                original_money = (
                    ((line_item.get("originalUnitPriceSet") or {}).get("shopMoney") or {})
                )
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
                        "unit_revenue": discounted_money.get("amount") or original_money.get("amount"),
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


def get_products(access_token: str, shop: str, page_size: int = 100) -> pd.DataFrame:
    query = """
    query Products($first: Int!, $after: String) {
      products(first: $first, after: $after, sortKey: UPDATED_AT, reverse: true) {
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
          }
        }
      }
    }
    """

    rows: list[dict[str, Any]] = []
    cursor: str | None = None

    while True:
        payload = _graphql_request(
            shop,
            access_token,
            query,
            {"first": page_size, "after": cursor},
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
                }
            )

        page_info = products.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")

    products_df = pd.DataFrame(rows)
    if not products_df.empty and "id" in products_df.columns:
        products_df = products_df.set_index("id")
    return products_df
