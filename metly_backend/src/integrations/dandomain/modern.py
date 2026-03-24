import httpx
import pandas as pd
import json


def getDandomainToken(tenant, client_id, client_secret):
    url = f"https://{tenant}.mywebshop.io/auth/oauth/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "",
    }
    response = httpx.post(url, data=data)

    token = response.json().get("access_token")

    return token


def getOrders(token, tenant, page_size: int = 100, max_pages: int = 1000):
    """Get orders via GraphQL and return pandas DataFrames for:
    - orders: each row is an order and contains a customer_id to join with customers
    - customers: unique customers found in the orders
    - order_lines: each row is an order line and contains order_id to join with orders
    - languages: unique languages found in the orders

    Returns: dict[str, pd.DataFrame]
    """
    url = f"https://{tenant}.mywebshop.io/api/graphql"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    # We'll page through results using the GraphQL pagination options.
    # The API expects orders(pagination:{limit: N, page: M})
    graphql_query = (
        "query Orders($page: Int, $limit: Int){"
        "orders(pagination: {page: $page, limit: $limit}){data{"
        "id, totalItems, total, currency{symbol}, createdAt,"
        "customer{id, billingAddress{firstName, lastName, addressLine, city, zipCode, email}, extendedData{internal, external}},"
        "orderLines{id, productTitle, variantTitle, amount, unitRevenue, unitCost, stock{status, amount}, productId}"
        "language{id, iso}"
        "}}}"
    )

    orders_list = []
    page = 1
    pages_fetched = 0
    page_size = 100

    while True:
        if pages_fetched >= max_pages:
            # safety break to avoid infinite loops against a buggy API
            break

        payload = {
            "query": graphql_query,
            "variables": {"page": page, "limit": page_size},
            "operationName": "Orders",
        }

        response = httpx.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            print(
                f"Warning: received status code {response.status_code} for page {page}"
            )
            page += 1
            continue

        payload_json = response.json()

        # extract this page's data
        try:
            page_items = payload_json.get("data", {}).get("orders", {}).get("data", [])
        except Exception:
            page_items = []

        if not page_items:
            break

        orders_list.extend(page_items)

        # stop if this page contains fewer items than requested (last page)
        if len(page_items) < page_size:
            break

        print(f"Fetched page {page} with {len(page_items)} orders")

        page += 1
        pages_fetched += 1

    orders_rows = []
    customers_map = {}
    order_lines_rows = []
    languages_map = {}

    for ord_item in orders_list:
        order_id = ord_item.get("id")

        # Customer handling
        cust = ord_item.get("customer") or {}
        cust_id = cust.get("id")
        # Language handling
        lang = ord_item.get("language") or {}
        lang_id = lang.get("id")
        lang_iso = lang.get("iso")
        if lang_id:
            languages_map[lang_id] = {"language_id": lang_id, "iso": lang_iso}
        # Flatten billing address and extended data for customer
        billing = cust.get("billingAddress") or {}
        extended = cust.get("extendedData") or {}

        if cust_id:
            # store/overwrite with latest occurrence (same customer across orders)
            customers_map[cust_id] = {
                "customer_id": cust_id,
                "billing_firstName": billing.get("firstName"),
                "billing_lastName": billing.get("lastName"),
                "billing_addressLine": billing.get("addressLine"),
                "billing_city": billing.get("city"),
                "billing_zipCode": billing.get("zipCode"),
                "billing_email": billing.get("email"),
                "extended_internal": extended.get("internal"),
                "extended_external": extended.get("external"),
            }

        # Order row (keep customer_id to join later)
        orders_rows.append(
            {
                "order_id": order_id,
                "totalItems": ord_item.get("totalItems"),
                "total": ord_item.get("total"),
                "currency_symbol": (ord_item.get("currency") or {}).get("symbol"),
                "createdAt": ord_item.get("createdAt"),
                "customer_id": cust_id,
                "language_id": lang_id,
            }
        )

        # Order lines
        for ol in ord_item.get("orderLines") or []:
            stock = ol.get("stock") or {}
            order_lines_rows.append(
                {
                    "order_line_id": ol.get("id"),
                    "order_id": order_id,
                    "product_id": ol.get("productId"),
                    "product_title": ol.get("productTitle"),
                    "variant_title": ol.get("variantTitle"),
                    "amount": ol.get("amount"),
                    "unit_revenue": ol.get("unitRevenue"),
                    "unit_cost": ol.get("unitCost"),
                    "stock_status": stock.get("status"),
                    "stock_amount": stock.get("amount"),
                }
            )

    # Build DataFrames
    orders_df = pd.DataFrame(orders_rows)
    customers_df = pd.DataFrame(list(customers_map.values()))
    order_lines_df = pd.DataFrame(order_lines_rows)
    languages_df = pd.DataFrame(list(languages_map.values()))

    # Ensure consistent dtypes / index
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


def getProducts(token, tenant):
    """Fetch products via GraphQL and return a single pandas DataFrame.

    Returns: dict[str, pd.DataFrame] with key "products"
    """
    url = f"https://{tenant}.mywebshop.io/api/graphql"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    payload = {
        "query": (
            "query {"
            "  product {"
            "    content {"
            "      id"
            "      articleNumber"
            "      ean"
            "      price"
            "      cost"
            "      discount"
            "      primaryProductCategoryId"
            "      secondaryCategories {"
            "        id"
            "        title"
            "      }"
            "      productSortingByCategory {"
            "        categoryId"
            "        sorting"
            "      }"
            "      brand {"
            "        id"
            "        name"
            "      }"
            "      totalStockAmount"
            "      createdAt"
            "      updatedAt"
            "    }"
            "  }"
            "}"
        ),
        "variables": {},
        "operationName": None,
    }
    response = httpx.post(url, headers=headers, json=payload)
    response.raise_for_status()

    payload_json = response.json()

    products_data = payload_json.get("data", {}).get("product", {}).get("content", [])
    
    # Flatten nested structures for DataFrame
    products_list = []
    for product in products_data:
        product_id = product.get("id")
        
        # Handle primary category
        primary_category_id = product.get("primaryProductCategoryId")
        
        # Handle secondary categories
        secondary_categories = product.get("secondaryCategories", [])
        secondary_category_ids = []
        secondary_category_titles = []
        for category in secondary_categories:
            secondary_category_ids.append(category.get("id"))
            secondary_category_titles.append(category.get("title"))
        
        # Handle product sorting by category
        sorting_by_category = product.get("productSortingByCategory", [])
        sorting_map = {}
        for sorting in sorting_by_category:
            sorting_map[sorting.get("categoryId")] = sorting.get("sorting")
        
        # Handle brand
        brand = product.get("brand", {})
        brand_id = brand.get("id")
        brand_name = brand.get("name")
        
        # Create product record
        products_list.append({
            "id": product_id,
            "articleNumber": product.get("articleNumber"),
            "ean": product.get("ean"),
            "price": product.get("price"),
            "cost": product.get("cost"),
            "discount": product.get("discount"),
            "primaryProductCategoryId": primary_category_id,
            "secondaryCategoryIds": ",".join(map(str, secondary_category_ids)),
            "secondaryCategoryTitles": ",".join(map(str, secondary_category_titles)),
            "sortingByCategoryId": json.dumps(sorting_map),
            "brandId": brand_id,
            "brandName": brand_name,
            "totalStockAmount": product.get("totalStockAmount"),
            "createdAt": product.get("createdAt"),
            "updatedAt": product.get("updatedAt"),
        })

    return {
        "products": pd.DataFrame(products_list)
    }


def getProductCategories(token, tenant):
    """Fetch product categories via GraphQL and return a single pandas DataFrame.

    Returns: dict[str, pd.DataFrame] with key "product_categories"
    """
    url = f"https://{tenant}.mywebshop.io/api/graphql"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    payload = {
        "query": ("query{productCategories{content{id, path, createdAt, updatedAt}}}"),
        "variables": {},
        "operationName": None,
    }

    response = httpx.post(url, headers=headers, json=payload)
    response.raise_for_status()

    payload_json = response.json()

    labels_query = (
        "query ProductCategoryTree($languageId: ID!){"
        "productCategoryTree(input: {languageId: $languageId}){"
        "content { id, title, updatedAt }"
        "errors { message }"
        "}"
        "}"
    )

    labels_payload = {
        "query": labels_query,
        "variables": {"languageId": "36"},
        "operationName": "ProductCategoryTree",
    }

    response_labels = httpx.post(url, headers=headers, json=labels_payload)
    response_labels.raise_for_status()

    labels_json = response_labels.json()

    # Build a map id->title from the category tree response (if available)
    labels_map = {}
    try:
        label_pc = labels_json.get("data", {}).get("productCategoryTree", {})
        label_items = label_pc.get("content", []) if isinstance(label_pc, dict) else []
        for li in label_items:
            if isinstance(li, dict) and li.get("id"):
                labels_map[li.get("id")] = li.get("title")
    except Exception:
        labels_map = {}

    items = []
    try:
        items = (
            payload_json.get("data", {}).get("productCategories", {}).get("content", [])
        )
    except Exception:
        items = []

    rows = []
    for it in items:
        rows.append(
            {
                "id": it.get("id"),
                "path": (
                    json.dumps(it.get("path")) if it.get("path") is not None else None
                ),
                "title": labels_map.get(it.get("id")),
                "createdAt": it.get("createdAt"),
                "updatedAt": it.get("updatedAt"),
                # attach human readable title if we have it from the tree
            }
        )

    product_category_df = pd.DataFrame(rows)
    if not product_category_df.empty and "id" in product_category_df.columns:
        product_category_df = product_category_df.set_index("id")

    return {"product_categories": product_category_df}


if __name__ == "__main__":
    tenant = "shop82308"
    client_id = "10"
    client_secret = "3OVeIpxuMbO5JkDOArkGe3HBdPqHIuhal3Kq3OcV"
    token = getDandomainToken(tenant, client_id, client_secret)

    orders = getOrders(token, tenant)
    for name, df in orders.items():
        print(f"DataFrame: {name}")
        print(f"Columns: {list(df.columns)}")
        print(f"Column types:\n{df.dtypes}")
        print(f"Index: {df.index.name}\n")

    product_categories = getProductCategories(token, tenant)
    for name, df in product_categories.items():
        print(f"DataFrame: {name}")
        print(f"Columns: {list(df.columns)}")
        print(f"Column types:\n{df.dtypes}")
        print(f"Index: {df.index.name}\n")
