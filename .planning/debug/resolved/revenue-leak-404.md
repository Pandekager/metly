---
status: resolved
trigger: "GET /api/revenue_leak_analysis returns 404 on production (ngrok)"
created: 2026-04-17T00:00:00Z
updated: 2026-04-17T00:00:00Z
---

## Current Focus
hypothesis: Router path double-prefix issue - route defined as "/api/revenue_leak_analysis" but include_router adds "/api" prefix, creating "/api/api/revenue_leak_analysis"
test: Fix route path in revenue_leak_analysis.py (remove /api prefix) and test locally
expecting: Endpoint should work at /api/revenue_leak_analysis after fix
next_action: Fix the route path in revenue_leak_analysis.py

## Symptoms
expected: API should return revenue leak analysis data with order counts, leak percentages, etc.
actual: HTTP 404 Not Found
errors: ["HTTP/2 404 93ms"]
reproduction: curl https://ropier-unduteously-maudie.ngrok-free.dev/api/revenue_leak_analysis
started: Just deployed Phase 21 backend endpoint

## Eliminated
- 

## Evidence
- timestamp: 2026-04-17
  checked: Backend endpoint routing configuration
  found: Route was defined as "/api/revenue_leak_analysis" but getData.py includes router with prefix="/api", creating double-prefix "/api/api/revenue_leak_analysis"
  implication: Fixed by removing /api prefix from route definition in revenue_leak_analysis.py
  verification: Tested with curl - got 401 (auth required) instead of 404, confirming route now registered correctly

- timestamp: 2026-04-17
  checked: Database schema
  found: orders table missing orderStatus and cancelledAt columns required by revenue_leak_analysis endpoint
  implication: Added orderStatus and cancelledAt columns to orders table via ALTER TABLE

- timestamp: 2026-04-17
  checked: Demo data generation
  found: demo.py wasn't generating orderStatus field for orders
  implication: Updated demo.py to generate orderStatus (3% payment_failed, 5% cancelled, 2% refunded, 90% completed) and include orderStatus/cancelledAt in INSERT

- timestamp: 2026-04-17
  checked: Full endpoint test
  found: Endpoint now returns 200 OK with revenue leak data
  verification: curl to /api/revenue_leak_analysis returns valid JSON with order counts and revenue data

## Resolution
root_cause: Double-prefix routing - route was defined as "/api/revenue_leak_analysis" but getData.py includes router with prefix="/api", creating "/api/api/revenue_leak_analysis" which didn't exist. Additionally, the orders table was missing orderStatus and cancelledAt columns.

fix: 1) Changed route in revenue_leak_analysis.py from "/api/revenue_leak_analysis" to "/revenue_leak_analysis" so final path is "/api/revenue_leak_analysis". 2) Added orderStatus and cancelledAt columns to orders table. 3) Updated demo.py to generate orderStatus data for demo orders.

verification: Endpoint returns 200 OK with valid revenue leak analysis JSON 
files_changed: 
- backend/src/endpoints/revenue_leak_analysis.py (removed /api prefix from route)
- backend/src/db/createTables.sql (added orderStatus and cancelledAt columns)
- backend/src/integrations/demo/demo.py (added orderStatus generation for demo data)