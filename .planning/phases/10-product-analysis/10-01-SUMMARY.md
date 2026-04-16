---
phase: 10-product-analysis
plan: '01'
subsystem: backend
tags:
  - product-analytics
  - ai-recommendations
  - api
dependency_graph:
  requires: []
  provides:
    - src/scripts/analysis/productAdvice.py
    - src/endpoints/productAnalytics.py
  affects:
    - main.py
tech_stack:
  added:
    - google.generativeai
    - pandas
  patterns:
    - Follows consultAi.py pattern for AI analysis
    - SQLAlchemy text() with parameterized queries
    - Multi-tenant isolation via user_id filtering
key_files:
  created:
    - backend/src/scripts/analysis/productAdvice.py
    - backend/src/endpoints/productAnalytics.py
    - frontend/types/product.ts
  modified:
    - backend/src/endpoints/getData.py
    - backend/main.py
decisions:
  - "Use 'product_business_advice' as ai_category_id for product AI responses"
  - "Query JOIN products + order_lines + orders tables for sales data"
  - "Return top 50 products ordered by revenue DESC"
metrics:
  duration: ~3 minutes
  completed: 2026-04-16T12:11:37Z
---

# Phase 10 Plan 01 Summary: Product Analytics Backend

## One-liner

Product analytics backend pipeline with AI-powered recommendations using Gemini, serving product sales data via REST API endpoints.

## Tasks Completed

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Create productAdvice.py analysis script | [0bb4356](https://github.com/rasmus-holmer/metly/commit/0bb4356) | productAdvice.py |
| 2 | Create product analytics API endpoints | [0bb4356](https://github.com/rasmus-holmer/metly/commit/0bb4356) | productAnalytics.py, getData.py |
| 3 | Update main.py to run product analysis | [0bb4356](https://github.com/rasmus-holmer/metly/commit/0bb4356) | main.py |
| 4 | Create TypeScript types for product data | [0bb4356](https://github.com/rasmus-holmer/metly/commit/0bb4356) | product.ts |

## What Was Built

### productAdvice.py
- `get_product_advice()` - Main function that queries product sales data and generates AI recommendations
- `prepare_product_summary()` - Formats product data for AI consumption (top sellers, categories, slow movers)
- `call_gemini_product_ai()` - Calls Gemini API with Danish prompt for pricing, bundling, inventory advice
- `save_ai_response()` - Stores responses with `product_business_advice` category in ai_responses table

### productAnalytics.py
- `GET /api/product_analytics` - Returns top products and monthly sales trends
- `GET /api/product_business_advice` - Returns stored AI recommendations for products
- All endpoints use JWT authentication and filter by user_id

### main.py
- Added step 6: "Running Product AI Analysis" after AI business advice step

## API Endpoints

| Endpoint | Response |
| -------- | -------- |
| `GET /api/product_analytics` | `{ top_products: ProductAnalytics[], sales_trends: ProductTrend[] }` |
| `GET /api/product_business_advice` | `{ response_text: string }` |

## Deviation Documentation

### Auto-fixed Issues
None - plan executed exactly as written.

## Threat Surface Scan

| Flag | File | Description |
|------|------|-------------|
| N/A | productAnalytics.py | SQL injection mitigated via parameterized queries with SQLAlchemy text() |
| N/A | productAnalytics.py | Multi-tenant isolation via user_id JWT filtering |

## Verification

- [x] productAdvice.py syntax verified with py_compile
- [x] productAnalytics.py syntax verified with py_compile
- [x] getData.py syntax verified with py_compile
- [x] main.py syntax verified with py_compile

## Self-Check: PASSED

All files created and syntax verified. Backend API endpoints registered and main.py updated.
