import unittest
from datetime import datetime, timezone

import pandas as pd

from src.integrations.shopify.shopify import _updated_since_query
from src.scripts.db.populateDB import _validate_shopify_payload


class ShopifyDeltaTests(unittest.TestCase):
    def test_updated_since_query_normalizes_to_utc(self):
        value = datetime(2026, 3, 30, 10, 15, 0, tzinfo=timezone.utc)
        self.assertEqual(
            _updated_since_query("updated_at", value),
            "updated_at:>=2026-03-30T10:15:00Z",
        )

    def test_validate_shopify_payload_rejects_missing_customer_dependency(self):
        orders = {
            "orders": pd.DataFrame(
                [
                    {
                        "order_id": "o1",
                        "customer_id": "c1",
                    }
                ]
            ).set_index("order_id"),
            "customers": pd.DataFrame([], columns=["customer_id"]).set_index("customer_id"),
            "order_lines": pd.DataFrame([], columns=["order_line_id"]).set_index("order_line_id"),
            "languages": pd.DataFrame([], columns=["language_id"]).set_index("language_id"),
        }

        with self.assertRaisesRegex(ValueError, "missing customers"):
            _validate_shopify_payload(orders, pd.DataFrame())

    def test_validate_shopify_payload_rejects_missing_order_dependency(self):
        orders = {
            "orders": pd.DataFrame(
                [
                    {
                        "order_id": "o1",
                        "customer_id": None,
                    }
                ]
            ).set_index("order_id"),
            "customers": pd.DataFrame([], columns=["customer_id"]).set_index("customer_id"),
            "order_lines": pd.DataFrame(
                [
                    {
                        "order_line_id": "ol1",
                        "order_id": "missing-order",
                        "product_id": "p1",
                    }
                ]
            ).set_index("order_line_id"),
            "languages": pd.DataFrame([], columns=["language_id"]).set_index("language_id"),
        }

        with self.assertRaisesRegex(ValueError, "missing orders"):
            _validate_shopify_payload(
                orders,
                pd.DataFrame([{"id": "p1", "product_name": "Product"}]).set_index("id"),
            )


if __name__ == "__main__":
    unittest.main()
