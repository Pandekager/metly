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