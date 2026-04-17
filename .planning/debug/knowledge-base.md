# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern hypotheses at the start of new investigations.

---

## revenue-leak-404 — GET /api/revenue_leak_analysis returns 404 on production
- **Date:** 2026-04-17
- **Error patterns:** 404, revenue_leak_analysis, ngrok, production
- **Root cause:** Double-prefix routing - route was defined as '/api/revenue_leak_analysis' but getData.py includes router with prefix='/api', creating '/api/api/revenue_leak_analysis'. Also, orders table was missing orderStatus and cancelledAt columns.
- **Fix:** Changed route in revenue_leak_analysis.py from '/api/revenue_leak_analysis' to '/revenue_leak_analysis' so final path is '/api/revenue_leak_analysis'. Added orderStatus and cancelledAt columns to orders table. Updated demo.py to generate orderStatus data.
- **Files changed:** backend/src/endpoints/revenue_leak_analysis.py, backend/src/db/createTables.sql, backend/src/integrations/demo/demo.py
---

## charts-no-data — Order Flow and Indtægtslækage tabs show 0 data
- **Date:** 2026-04-17
- **Error patterns:** Order Flow, Indtægtslækage, 0 data, charts empty, fulfillment_status, tracking, carrier
- **Root cause:** Orders INSERT statement in both demo.py and populateDB.py did not include order flow fields (processed_at, fulfilled_at, cancelled_at, closed_at, fulfillment_status, tracking_number, carrier). These fields were generated but never inserted. Shopify integration was also missing fulfillment/tracking data from GraphQL query.
- **Fix:** Updated demo.py and populateDB.py INSERT statements to include all order flow fields. Added fulfillments/trackingInfo to Shopify GraphQL query and extraction logic.
- **Files changed:** backend/src/integrations/demo/demo.py, backend/src/scripts/db/populateDB.py, backend/src/integrations/shopify/shopify.py
---

## refund-return-500 — GET /api/refund_return_analysis returns 500 error
- **Date:** 2026-04-17
- **Error patterns:** 500, refund_return_analysis, closedAt, closed_at, quantity, amount, price, unit_revenue
- **Root cause:** Multiple column name mismatches in SQL queries - query used camelCase/snake_case incorrectly and wrong column names (closedAt→closed_at, quantity→amount, price→unit_revenue, p.name→p.product_name). Demo data also had old records without proper order statuses.
- **Fix:** Fixed all column names to match actual database schema. Regenerated demo data for user with proper order status distribution (3% failed, 5% cancelled, 2% refunded, 90% completed) and fulfillment timestamps.
- **Files changed:** backend/src/endpoints/refund_return_analysis.py, backend/src/integrations/demo/demo.py
---