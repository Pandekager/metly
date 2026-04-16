# Phase 10: Product Analysis Feature - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Add product analytics and AI-powered recommendations to the "produkter" tab in home.vue. For each connected webshop, display sales metrics and provide AI-driven recommendations on product optimization. This feature integrates with populateDB.py for data processing.
</domain>

<decisions>
## Implementation Decisions

### Analytics Content
- **D-01:** Display units sold, revenue per product, and sales trends over time in the produkter tab
- **D-02:** Include top-selling products table with key metrics
- **D-03:** Use charts to visualize sales trends (similar to forecast chart pattern)

### AI Recommendation Scope
- **D-04:** AI provides full recommendations including: pricing optimization, bundling opportunities, slow-moving products, inventory recommendations
- **D-05:** AI response format similar to existing `AIBusinessAdvice` component pattern
- **D-06:** AI category identifier: `product_business_advice`

### Frontend Presentation
- **D-07:** Layout: Charts (sales trends) + Table (top products) + AI recommendation panel below
- **D-08:** Reuse existing `AIBusinessAdvice.vue` component for AI display
- **D-09:** Reuse existing chart components from `components/charts/` for product trends

### Data Integration
- **D-10:** Analyze product catalog data (from `products` table) + order line sales data (from `order_lines` table)
- **D-11:** Focus on Shopify data source for this implementation
- **D-12:** Query structure: JOIN products with order_lines to get sales metrics per product

### Backend Pipeline
- **D-13:** New analysis function in `src/scripts/analysis/` similar to `consultAi.py` structure
- **D-14:** Data aggregation via populateDB.py - pre-calculate product metrics during data fetch
- **D-15:** Store AI responses in `ai_responses` table with category `product_business_advice`

### Agent's Discretion
- Specific chart types (bar, line, pie) - use existing chart components
- Table sorting/filtering UI - standard approach
- AI prompt specifics - follow existing consultAi pattern

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Patterns
- `backend/src/scripts/analysis/consultAi.py` — AI business advice pattern to replicate for products
- `frontend/components/AIBusinessAdvice.vue` — Reusable AI advice display component
- `frontend/pages/home.vue` — Dashboard structure, tab system, data fetching pattern
- `frontend/components/charts/ForecastChart.vue` — Chart component to reuse for product trends

### Data Models
- `backend/src/db/createTables.sql` — products, order_lines, ai_responses table schemas

### Integration Points
- `backend/src/endpoints/getData.py` — API endpoints for frontend data fetching
- `backend/src/scripts/db/populateDB.py` — Data aggregation pipeline
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AIBusinessAdvice.vue` — Already handles AI advice display with similar format needed for products
- `ForecastChart.vue` — Chart component pattern for sales visualization
- `consultAi.py` — Complete pattern for AI business advice (query → Gemini → save → API)

### Established Patterns
- Tab-based UI in home.vue with separate content per tab (ordrer, kunder, produkter)
- Data fetching via `$fetch()` to `/api/` endpoints
- AI advice stored in `ai_responses` table with category identifier

### Integration Points
- New API endpoint needed: `/api/product_business_advice` (similar to `/api/forecast_business_advice`)
- New analysis script: `src/scripts/analysis/productAdvice.py`
- Update `populateDB.py` to run product analysis after data sync
</code_context>

<specifics>
## Specific Ideas

- Shopify-first implementation (per user note about focusing on Shopify data)
- AI should provide actionable recommendations in Danish (same as existing consultAi)
- Reuse existing components rather than creating new ones where possible
</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope
</deferred>

---

*Phase: 10-product-analysis*
*Context gathered: 2026-04-16*