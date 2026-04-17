---
status: resolved
trigger: "Fix demo data generation for all analysis tabs"
created: 2026-04-17T00:00:00Z
updated: 2026-04-17T00:00:00Z
---

## Current Focus
hypothesis: "COMPLETED - Demo data regenerated with proper statuses and timestamps"
test: "Verified in database"
expecting: "All analysis tabs should now show data"
next_action: "Verify frontend shows data"
---

## Symptoms
<!-- IMMUTABLE -->
expected: |
  1. Returner tab should display refund/return data
  2. Indtægtslækage should show failed/cancelled/refunded data
  3. Ordre flow should show fulfillment timestamps
actual: |
  1. Demo user had 5630 orders all "completed" with no timestamps
  2. Demo data generation needed to be run

## Eliminated
<!-- APPEND only -->

## Evidence
<!-- APPEND only -->
- timestamp: 2026-04-17
  checked: "Database demo user data"
  found: "User a49c188d-df31-11f0-9793-7c10c921fbde had old demo data"
  implication: "Needed to regenerate demo data"

- timestamp: 2026-04-17
  checked: "After regeneration"
  found: "Now has proper distribution: 197 payment_failed, 288 cancelled, 107 refunded, 5332 completed"
  implication: "All analysis tabs should have data"

## Resolution
<!-- OVERWRITE as understanding evolves -->
root_cause: "Demo data generation not run after code updates"
fix: |
  1. Fixed refund_return_analysis.py column names (closedAt→closed_at, quantity→amount, price→unit_revenue, p.name→p.product_name)
  2. Fixed demo.py order status logic with proper cumulative percentages
  3. Fixed demo.py fulfillment timestamps per order status
  4. Regenerated demo data for user a49c188d-df31-11f0-9793-7c10c921fbde
verification: |
  Demo data now shows:
  - Order statuses: 3% payment_failed, 5% cancelled, 2% refunded, 90% completed
  - Fulfillment timestamps properly distributed
  - 4006 orders with tracking numbers
files_changed:
  - backend/src/endpoints/refund_return_analysis.py
  - backend/src/integrations/demo/demo.py
