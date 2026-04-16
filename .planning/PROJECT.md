# Metly Project

**Last Updated:** 2026-04-16 after v1.0 milestone

## What This Is

Metly is an e-commerce analytics dashboard that connects to webshop platforms (Shopify, Dandomain) and provides AI-powered business insights through sales forecasting, customer analytics, and product performance analysis.

## Core Value

AI-driven business intelligence for small to medium e-commerce stores — turning raw sales data into actionable recommendations.

## Requirements

### Validated

(None yet — first milestone)

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

**v1.0 Shipped:**
- Product analytics tab with sales trends and top products
- AI-powered product recommendations (pricing, bundling, inventory)
- Shopify test data generator for development

## Key Decisions

| Decision | Outcome |
|----------|---------|
| Reuse existing AIBusinessAdvice pattern for product AI | ✓ Implemented |
| Shopify-first for product data focus | ✓ Implemented |
| Tab-based dashboard layout | ✓ Shipped |

---

*Last updated: 2026-04-16 after v1.0 milestone*