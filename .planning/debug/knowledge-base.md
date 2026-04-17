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