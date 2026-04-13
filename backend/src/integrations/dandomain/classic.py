import requests
import re
from datetime import datetime, timezone, timedelta
import pandas as pd
import base64


def _parse_dandomain_date(s: str) -> str:
    if not s:
        return "Ingen dato"
    m = (
        re.match(
            r"/Date\((?P<ms>-?\d+)(?P<tzsign>[+-])?(?P<tzh>\d{2})?(?P(tzm)\d{2})?\)/",
            s,
        )
        if False
        else None
    )
    # safer regex (handles optional timezone like +0200)
    m = re.match(
        r"/Date\((?P<ms>-?\d+)(?P<tzsign>[+-])?(?P<tzh>\d{2})?(?P<tzm>\d{2})?\)/",
        s,
    )
    if not m:
        return s
    ms = int(m.group("ms"))
    tzsign = m.group("tzsign")
    tzh = m.group("tzh")
    tzm = m.group("tzm") or "00"
    dt_utc = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    if tzsign and tzh:
        off_minutes = int(tzh) * 60 + int(tzm)
        if tzsign == "-":
            off_minutes = -off_minutes
        tz = timezone(timedelta(minutes=off_minutes))
        dt = dt_utc.astimezone(tz)
    else:
        dt = dt_utc
    return dt.strftime("%Y-%m-%d %H:%M:%S %z")


# Testfunktion til at kontrollere forbindelsen til Dandomain Classic API'et
def testDandomainClassicConnection(api_key, tenant):

    SERVICE_ENDPOINT = f"{tenant}/admin/webapi/Endpoints/v1_0/OrderService"
    now = datetime.now()
    prev_month_last = now.replace(day=1) - timedelta(days=1)
    START_DATE = prev_month_last.replace(
        day=min(now.day, prev_month_last.day)
    ).strftime("%Y-%m-%d")
    END_DATE = now.strftime("%Y-%m-%d")

    request_url = (
        f"{SERVICE_ENDPOINT}/{api_key}/GetByDateInterval"
        f"?start={START_DATE}&end={END_DATE}"
    )

    print(f"Forsøger at forbinde til: {SERVICE_ENDPOINT}")
    print(f"Datointerval: {START_DATE} til {END_DATE}")

    try:
        # Sender GET-forespørgslen til Dandomain API'et
        response = requests.get(request_url, timeout=10)

        # Tjekker HTTP-statuskoden
        if response.status_code == 200:
            print("\n✅ FORBINDELSE LYKKEDES (Status 200 OK)!")

            # Forsøger at afkode svaret som JSON
            try:
                orders_data = response.json()
                print(f"Antal ordrer fundet: {len(orders_data)}")

                created_raw = orders_data[0].get("createdDate") if orders_data else None
                print(
                    f"Første ordre-createdDate: {_parse_dandomain_date(created_raw) if created_raw else 'Ingen ordrer i perioden'}"
                )
                print("\nDu er klar til at trække data!")

            except requests.exceptions.JSONDecodeError:
                # API'et returnerer nogle gange XML eller en ren fejltekst i stedet for JSON ved fejl
                print("\n⚠️ ADVARSEL: Svaret var ikke JSON.")
                print("Rå Svar (se efter en fejlbesked):")
                print(
                    response.text[:500] + "..."
                )  # Printer de første 500 tegn af svaret

        else:
            # Håndterer almindelige fejl som 401 (Uautoriseret) eller 404 (Ikke fundet)
            print(f"\n❌ FEJL VED FORBINDELSE! Statuskode: {response.status_code}")
            print("Fejlbesked fra Dandomain:")
            print(response.text)

            if response.status_code == 401:
                print(
                    "\n**Mulig årsag:** API-nøglen er ugyldig, eller rettighederne er forkerte."
                )
            elif response.status_code == 404:
                print("\n**Mulig årsag:** Webshop-URL'en eller EndPoint er forkert.")

    except requests.exceptions.RequestException as e:
        print(f"\nFATAL FORBINDELSESFEJL: Kunne ikke oprette forbindelse til serveren.")
        print(f"Kontrollér SHOP_URL: {e}")


def getOrders(
    api_key, tenant, max_pages: int = 50, latest_order_date: str = "9999-12-31 23:59:59"
):
    """Get orders via classic API and return pandas DataFrames for:
    - orders: each row is an order and contains a customer_id to join with customers
    - customers: unique customers found in the orders
    - order_lines: each row is an order line and contains order_id to join with orders
    - languages: unique languages found in the orders

    Returns: dict[str, pd.DataFrame]
    """

    orders_list = []
    now = datetime.now()
    months_fetched = 0
    SERVICE_ENDPOINT = f"{tenant}/admin/webapi/Endpoints/v1_0/OrderService"

    def _shift_months(dt: datetime, months: int) -> datetime:
        # subtract `months` months from dt, keeping day if possible
        tm_index = dt.year * 12 + dt.month - 1 - months
        target_year = tm_index // 12
        target_month = tm_index % 12 + 1
        # compute last day of target month
        if target_month == 12:
            next_month = datetime(target_year + 1, 1, 1)
        else:
            next_month = datetime(target_year, target_month + 1, 1)
        last_day = (next_month - timedelta(days=1)).day
        day = min(dt.day, last_day)
        return datetime(
            target_year,
            target_month,
            day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            dt.tzinfo,
        )

    while True:
        if months_fetched >= max_pages:
            # safety break to avoid infinite loops against a buggy API
            break

        # shift both start and end by months_fetched
        end_dt = _shift_months(now, months_fetched)
        prev_month_last = end_dt.replace(day=1) - timedelta(days=1)
        start_dt = prev_month_last.replace(day=min(end_dt.day, prev_month_last.day))
        START_DATE = start_dt.strftime("%Y-%m-%d")
        END_DATE = end_dt.strftime("%Y-%m-%d")
        latest_order_date = datetime.fromisoformat(str(latest_order_date)).strftime(
            "%Y-%m-%d"
        )

        request_url = (
            f"{SERVICE_ENDPOINT}/{api_key}/GetByDateInterval"
            f"?start={START_DATE}&end={END_DATE}"
        )

        response = requests.get(request_url, timeout=30)

        # Tjekker HTTP-statuskoden
        if response.status_code == 200:
            print(f"Fetched orders for period {START_DATE} to {END_DATE}")
            orders_data = response.json()
            orders_list.extend(orders_data)

            if len(orders_data) == 0:
                # no more data
                break

            # TODO: This is ready to just get the latest orders, but I need to
            # modify customers and order_lines extraction to handle partial data
            if latest_order_date and START_DATE < latest_order_date:
                # reached already fetched data
                break

        if response.status_code != 200:
            print(
                f"Warning: received status code {response.status_code} for period {START_DATE} to {END_DATE}"
            )
            break

        months_fetched += 1

    orders_rows = []
    customers_map = {}
    order_lines_rows = []
    languages_map = {}

    for ord_item in orders_list:
        order_id = ord_item.get("id")

        # Dates
        created_raw = ord_item.get("createdDate") or ord_item.get("modifiedDate")
        created_at = _parse_dandomain_date(created_raw) if created_raw else None

        # Totals / counts (be resilient to different field names)
        total_items = sum(
            int(ol.get("quantity") or ol.get("amount") or 0)
            for ol in ord_item.get("orderLines") or []
        )
        total = (
            ord_item.get("total") or ord_item.get("totalPrice") or ord_item.get("total")
        )
        currency = ord_item.get("currencyCode") or (ord_item.get("currency") or {}).get(
            "symbol"
        )

        # Customer: classic examples sometimes use "customerInfo"
        cust = ord_item.get("customer") or ord_item.get("customerInfo") or {}
        cust_id = cust.get("id")
        # billing/delivery: prefer explicit billingAddress if present, else use customerInfo fields
        billing = cust.get("billingAddress") or {}
        if not billing:
            # map customerInfo fields to billing-like keys (handle missing attention and return lastName as string)
            attention = cust.get("attention") or ""
            parts = attention.split(None, 1) if attention else []
            billing = {
                "firstName": parts[0] if parts else None,
                "lastName": parts[1] if len(parts) > 1 else None,
                "city": cust.get("city"),
                "zipCode": cust.get("zipCode"),
                "email": cust.get("email"),
                "phone": cust.get("phone"),
            }

        # Language/site
        lang = ord_item.get("language") or {}
        lang_id = lang.get("id") or ord_item.get("siteId")

        # Store customer (overwrite with latest occurrence)
        if cust_id:
            customers_map[str(cust_id)] = {
                "customer_id": str(cust_id),
                "billing_firstName": billing.get("firstName"),
                "billing_lastName": billing.get("lastName"),
                "billing_attention": billing.get("attention"),
                "billing_addressLine": billing.get("addressLine"),
                "billing_city": billing.get("city"),
                "billing_zipCode": billing.get("zipCode"),
                "billing_email": billing.get("email"),
                "billing_phone": billing.get("phone"),
            }

        # Order-level fields (flatten useful bits)
        orders_rows.append(
            {
                "order_id": order_id,
                "totalItems": total_items,
                "total": total,
                "currency": currency,
                "createdAt": created_at,
                "customer_id": str(cust_id) if cust_id is not None else None,
                "language_id": lang_id,
                "order_state_id": (ord_item.get("orderState") or {}).get("id"),
                "order_state_name": (ord_item.get("orderState") or {}).get("name"),
                "payment_method": (ord_item.get("paymentInfo") or {}).get("name"),
                "shipping_method": (ord_item.get("shippingInfo") or {}).get("name"),
                "invoice_state": (ord_item.get("invoiceInfo") or {}).get("state"),
                "site_id": ord_item.get("siteId"),
                "ip": ord_item.get("ip"),
                "referrer": ord_item.get("referrer"),
                "totalWeight": ord_item.get("totalWeight"),
                "trackingNumber": ord_item.get("trackingNumber"),
            }
        )

        # Order lines: handle differences in field names between examples
        for ol in ord_item.get("orderLines") or []:
            product_id = (
                ol.get("productId") or ol.get("product_id") or ol.get("product")
            )
            product_title = (
                ol.get("productTitle")
                or ol.get("productName")
                or ol.get("product_name")
            )
            variant_title = ol.get("variantTitle") or ol.get("variant")
            amount = ol.get("amount") or ol.get("quantity") or ol.get("qty")
            unit_revenue = (
                ol.get("unitRevenue") or ol.get("unitPrice") or ol.get("unit_price")
            )
            total_price = ol.get("totalPrice") or ol.get("total") or None
            vat = ol.get("vatPct") or ol.get("vat") or None

            order_lines_rows.append(
                {
                    "order_line_id": ol.get("id"),
                    "order_id": order_id,
                    "product_id": product_id,
                    "product_title": product_title,
                    "variant_title": variant_title,
                    "amount": amount,
                    "unit_revenue": unit_revenue,
                    "total_price": total_price,
                    "vat_pct": vat,
                    "unit_cost": ol.get("unitCost"),
                    # stock fields may not exist in Classic responses
                    "stock_status": (ol.get("stock") or {}).get("status"),
                    "stock_amount": (ol.get("stock") or {}).get("amount"),
                    "fileUrl": ol.get("fileUrl"),
                    "xmlParams": ol.get("xmlParams"),
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


def getProducts(api_key, tenant):
    """Fetch categories and products from Dandomain Classic ProductService.
    See: https://support.dandomain.dk/webshop-hjaelp/api/api-documentation/api-product/
    """

    # Define parameters
    SERVICE_ENDPOINT = f"{tenant}/admin/WebAPI/v2"
    site_category = 45  # Houmann.dk main category ID

    # use Basic auth "metly:{api_key}" as in the curl example
    basic_token = base64.b64encode(f"metly:{api_key}".encode()).decode()
    headers = {"accept": "text/plain", "Authorization": f"Basic {basic_token}"}

    # Fetch all main categories with pagination
    categories_list = []
    limit = 100
    offset = 0
    while True:
        request_main_categories = f"{SERVICE_ENDPOINT}/sites/{site_category}/categories?notHidden=true&limit={limit}&offset={offset}"
        response_main_categories = requests.get(
            request_main_categories, headers=headers, timeout=30
        )
        try:
            categories_data = response_main_categories.json()
        except Exception:
            # fall back to raw text if not JSON
            categories_data = response_main_categories.text

        # Normalize raw JSON into a list
        if isinstance(categories_data, dict):
            # handle responses that wrap items in a top-level key
            if "items" in categories_data:
                raw_list = categories_data.get("items") or []
            elif "categories" in categories_data:
                raw_list = categories_data.get("categories") or []
            else:
                raw_list = [categories_data]
        else:
            raw_list = categories_data or []

        if not raw_list:
            break  # No more data

        categories_list.extend(raw_list)
        offset += limit

        # Stop if fewer items than limit (last page)
        if len(raw_list) < limit:
            break

    # Create a flat dataframe from all collected categories
    categories_df = pd.json_normalize(categories_list)[["id", "name"]].drop_duplicates()

    # Get sub-categories for each main category
    subcategories_df = pd.DataFrame()
    subcategories_df_temp = pd.DataFrame()

    # Loop over each main category and page through its subcategories
    limit = 100
    for _, main_id in enumerate(categories_df["id"].dropna().unique()):
        offset = 0
        if _ % 100 == 0:
            print(
                f"{_+1}/{len(categories_df)}: Fetching subcategories for main category ID {main_id}"
            )
        while True:
            request_sub_categories = (
                f"{SERVICE_ENDPOINT}/sites/{site_category}/categories/{main_id}/categories"
                f"?notHidden=true&limit={limit}&offset={offset}"
            )
            response_sub = requests.get(
                request_sub_categories, headers=headers, timeout=10
            )
            try:
                sub_json = response_sub.json()
            except Exception:
                # if response is not JSON or on error, stop paging this category
                break

            # Normalize sub_json into a list of items
            items = sub_json["items"]

            if not items:
                break

            # Attach parent (main) category id to each subcategory item
            for itm in items:
                if isinstance(itm, dict):
                    subcategories_df_temp = pd.DataFrame(
                        {
                            "id": [itm.get("id")],
                            "name": [itm.get("name")],
                            "parent_category": [main_id],
                        }
                    )
                    subcategories_df = pd.concat(
                        [subcategories_df, subcategories_df_temp], ignore_index=True
                    )
                else:
                    # unexpected item type, skip
                    continue

            offset += limit
            if len(items) < limit:
                break

    # Fetch products for each subcategory
    df_products = pd.DataFrame()
    df_products_temp = pd.DataFrame()

    limit = 100
    if not subcategories_df.empty:
        for _, sub_id in enumerate(subcategories_df["id"].dropna().unique()):
            if _ % 100 == 0:
                print(
                    f"{_+1}/{len(subcategories_df)}: Fetching products for subcategory ID {sub_id}"
                )
            offset = 0
            while True:
                request_products = (
                    f"{SERVICE_ENDPOINT}/sites/{site_category}/categories/{sub_id}/products"
                    f"?currency=DKK&notHidden=true&limit={limit}&offset={offset}"
                )
                resp = requests.get(request_products, headers=headers, timeout=15)
                if resp.status_code != 200:
                    break
                try:
                    prod_data = resp.json()
                except Exception:
                    break

                # Normalize prod_data into a list of items
                items = prod_data["items"]

                if not items:
                    break

                # Attach parent (main) category id to each subcategory item
                for itm in items:
                    if isinstance(itm, dict):
                        df_products_temp = pd.DataFrame(
                            {
                                "productNumber": [itm.get("productNumber")],
                                "productName": [itm.get("name")],
                                "subcategory_id": [sub_id],
                                "maincategory_id": [main_id],
                            }
                        )
                        df_products = pd.concat(
                            [df_products, df_products_temp], ignore_index=True
                        )
                    else:
                        # unexpected item type, skip
                        continue

                offset += limit
                if len(items) < limit:
                    break

        if not df_products.empty:
            # try to align dtypes to improve merge robustness
            try:
                df_products["subcategory_id"] = df_products["subcategory_id"].astype(
                    subcategories_df["id"].dtype
                )
            except Exception:
                pass
            try:
                df_products["maincategory_id"] = df_products["maincategory_id"].astype(
                    categories_df["id"].dtype
                )
            except Exception:
                pass

            # merge subcategory name
            df_products = df_products.merge(
                subcategories_df[["id", "name"]].rename(
                    columns={"id": "subcategory_id", "name": "subcategory_name"}
                ),
                on="subcategory_id",
                how="left",
            )

            # merge main category name
            df_products = df_products.merge(
                categories_df[["id", "name"]].rename(
                    columns={"id": "maincategory_id", "name": "maincategory_name"}
                ),
                on="maincategory_id",
                how="left",
            )

    return df_products


if __name__ == "__main__":
    api_key = "4ad915ba-fb72-46fa-961e-89378eb4c984"
    tenant = "https://houmann.dk"
    latest_order_date = "2025-11-17 16:54:11"
    # testDandomainClassicConnection(api_key, tenant)
    orders = getOrders(
        api_key, tenant, max_pages=1, latest_order_date=latest_order_date
    )
