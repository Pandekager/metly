# Metly Project Roadmap

**Last Updated:** 2026-04-16

---

## Phase 10: Product Analysis Feature

**Goal:** Add product analytics and AI-powered recommendations to the "produkter" tab in home.vue.

**Status:** Ready for planning

**Plans:** 2 plans in 2 waves

### Requirements
- [AUTH-01 through AUTH-05, AUTH-11, AUTH-12] — Authentication and user management
- [CORE-01] — Dashboard with tab-based navigation
- [ANALYTICS-01] — Sales analytics and forecasting
- [ANALYTICS-02] — Business intelligence and recommendations

### Decision Coverage

| D-ID | Decision | Plan | Task |
|------|----------|------|------|
| D-01 | Display units sold, revenue per product, sales trends | 10-01, 10-02 | All tasks |
| D-02 | Top-selling products table with key metrics | 10-02 | Task 2 |
| D-03 | Use charts to visualize sales trends | 10-02 | Task 1 |
| D-04 | AI recommendations: pricing, bundling, slow movers, inventory | 10-01 | Task 1 |
| D-05 | AI response format similar to AIBusinessAdvice pattern | 10-01 | Task 1 |
| D-06 | AI category identifier: product_business_advice | 10-01 | Tasks 1, 2 |
| D-07 | Layout: Charts + Table + AI panel | 10-02 | Task 3 |
| D-08 | Reuse AIBusinessAdvice.vue for AI display | 10-02 | Task 3 |
| D-09 | Reuse existing chart components pattern | 10-02 | Task 1 |
| D-10 | Analyze products + order_lines tables | 10-01 | Task 2 |
| D-11 | Focus on Shopify data source | 10-01 | Task 1 |
| D-12 | JOIN products with order_lines query | 10-01 | Task 2 |
| D-13 | New analysis function similar to consultAi.py | 10-01 | Task 1 |
| D-14 | Data aggregation via populateDB.py | 10-01 | Task 4 |
| D-15 | Store AI responses with product_business_advice category | 10-01 | Task 1 |

### Plans

- [ ] 10-01-PLAN.md — Backend Product Analysis Pipeline (wave 1, autonomous)
- [ ] 10-02-PLAN.md — Frontend Product Analytics UI (wave 2, has checkpoint)

---

## Completed Phases

*(No completed phases yet)*

---

*Roadmap updated: 2026-04-16*
