# Phase 99: Shopify Test Data Generator - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Create a scheduled feature that generates fake Shopify test data (products, customers, orders) in a Danish golf store theme and syncs it to the metly database. The data is used for development and testing.

</domain>

<decisions>
## Implementation Decisions

### Data Generation
- **D-01:** Generate Danish golf products first, then generate orders with those products
- **D-02:** Product categories: golf clubs, golf bags, golf balls, gloves, golf apparel, accessories
- **D-03:** Customer data in Danish (names, addresses, cities)
- **D-04:** Order values realistic for golf retail (500-5000 DKK)

### Schedule
- **D-05:** Run daily (cron job) - frequency: `0 0 * * *`
- **D-06:** Use existing Shopify credentials from `.env`

### Integration
- **D-07:** Use Shopify Admin GraphQL API for creating data
- **D-08:** Sync data to metly via existing `populateDB` flow

</decisions>

<canonical_refs>
## Canonical References

### Existing Code
- `src/integrations/shopify/shopify.py` — Shopify API client (reads only)
- `src/scripts/db/populateDB.py` — Database population logic
- `backend/.env` — Shopify credentials

### External
- [Shopify Admin API - Orders Create](https://shopify.dev/docs/api/admin-rest/2025-10/resources/order) — GraphQL mutation for order creation

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `get_orders()` — reads from Shopify, shows the query pattern
- `get_products()` — reads products, shows data structure
- `populateDB()` — syncs to database

### Established Patterns
- Uses GraphQL with `X-Shopify-Access-Token`
- Uses `orders/create` mutation

</code_context>

<specifics>
## Specific Ideas

- Store name: "Metly Test Golf" (Danish)
- Product names in Danish: "Golfkølle", "Golfbold", "Golftaske", etc.
- Customer cities: København, Aarhus, Odense, Aalborg, Esbjerg
- Danish currency: DKK

</specifics>

<deferred>
## Deferred Ideas

- None — all scope captured

</deferred>
---

*Phase: 99-shopify-test-data*
*Context gathered: 2026-04-13*