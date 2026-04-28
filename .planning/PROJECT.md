# Metly Project

**Last Updated:** 2026-04-28 after v1.2 milestone

## What This Is

Metly is an e-commerce analytics dashboard that connects to webshop platforms (Shopify, Dandomain) and provides AI-powered business insights through sales forecasting, customer analytics, product performance analysis, and data-driven recommendations — with an intuitive dashboard featuring info tooltips and a unified timeline filter.

## Core Value

AI-driven business intelligence for small to medium e-commerce stores — turning raw sales data into actionable recommendations.

## Requirements

### Validated

- [x] v1.0: Product Analytics + Test Data (2026-04-16)
- [x] v1.1: Shopify Process Insights (2026-04-26)
- [x] v1.2: Data Fixes + UI Enhancements (2026-04-28)

### Active

- [ ] Multi-platform support (Shopify, Dandomain, Demo)
- [ ] Real-time data sync from e-commerce platforms
- [ ] Customer analytics with geographic visualization
- [ ] Product performance tracking and recommendations

### Out of Scope

- Mobile app — web-based dashboard approach
- Payment processing — read-only integrations
- Inventory management — sales analytics only

## Context

**Tech Stack:**
- Frontend: Nuxt 4 (Vue 3), TypeScript, Tailwind CSS, Chart.js
- Backend: FastAPI, Python 3.11+, SQLAlchemy, pandas, scikit-learn
- Database: MySQL (metlydk_main)
- AI: Google Gemini for business recommendations

**v1.2 Shipped (2026-04-28):**
- All 10 dashboard tabs loading data correctly for demo user
- Info icons with contextual tooltips on each tab
- Timeline date picker filtering all non-forecast tabs
- Consistent API routing (/api prefix) across all endpoints
- Blue/purple chart color palette with rounded bar corners
- Optimized refund/return analysis (daily data, AVG, product filter)
- Dynamic loading bar instead of spinner
- Dark mode fixes across all chart components
- Fixed inflated refund rate calculation (sums to 400% → max 33%)

## Key Decisions

| Decision | Outcome |
|----------|---------|
| Reuse existing AIBusinessAdvice pattern for product AI | ✓ Implemented |
| Shopify-first for product data focus | ✓ Implemented |
| Tab-based dashboard layout | ✓ Shipped |
| Centralize demo data in demo.py | ✓ Implemented in v1.1 |
| Blue/purple chart palette for all visualizations | ✓ Implemented in v1.2 |
| Dynamic loading bar over static spinner | ✓ Implemented in v1.2 |

---

*Last updated: 2026-04-27 for v1.2 milestone*