---
phase: 26
plan: 26-01
subsystem: insights-dashboard
tags: [dashboard, insights, recommendations, unified-view]
dependency_graph:
  requires:
    - Phase 20: Order Flow Analysis
    - Phase 21: Revenue Leak Detection
    - Phase 22: Refund & Return Analysis
    - Phase 23: Checkout Drop-off Analysis
    - Phase 24: Operational Bottlenecks
    - Phase 25: Customer Behavior Insights
  provides:
    - insights_dashboard API endpoint
    - InsightsDashboard.vue component
    - Indsigt tab in home.vue
  affects:
    - backend/src/endpoints/getData.py
tech_stack:
  added:
    - FastAPI endpoint with aggregated data model
    - Vue 3 component with reactive state
  patterns:
    - Aggregation pattern: combining data from multiple analysis sources
    - Priority-based recommendations with severity classification
    - Dark mode support with Tailwind CSS
key_files:
  created:
    - backend/src/endpoints/insights_dashboard.py
    - frontend/components/charts/InsightsDashboard.vue
    - frontend/server/api/insights_dashboard.get.ts
  modified:
    - backend/src/endpoints/getData.py
    - frontend/pages/home.vue
decisions:
  - Used severity thresholds for classifying leaks, bottlenecks, and refund rates
  - Priority 1-5 scale for recommendations (1 = highest priority)
  - Category-based grouping for recommendations (revenue, operations, retention, products)
metrics:
  duration: "~20 minutes"
  completed: "2026-04-26"
---

# Phase 26 Plan 26-01: Insights Dashboard Summary

## One-Liner

Unified Insights Dashboard aggregating revenue leaks, bottlenecks, refund products, and retention metrics into prioritized actionable recommendations.

## Completed Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Backend insights_dashboard.py endpoint | af7c801 | backend/src/endpoints/insights_dashboard.py, backend/src/endpoints/getData.py |
| 2 | InsightsDashboard.vue component | af7c801 | frontend/components/charts/InsightsDashboard.vue, frontend/server/api/insights_dashboard.get.ts |
| 3 | Add Indsigt tab to home.vue | af7c801 | frontend/pages/home.vue |

## What Was Built

### Backend (`insights_dashboard.py`)
- Aggregates data from all previous analysis phases (20-25)
- Calculates top revenue leak sources with severity classification (high >10%, medium >5%)
- Identifies operational bottlenecks with delay rates and severity
- Lists top refunded products by count and rate
- Computes key retention metrics: LTV, retention rate, one-time customer %
- Generates prioritized actionable recommendations based on data patterns
- Returns structured response with all insights

### Frontend (`InsightsDashboard.vue`)
- Displays summary stats: total orders, revenue, leak revenue, leak rate
- Shows prioritized recommendations with category badges and impact indicators
- Revenue leaks section with severity badges and percentages
- Retention metrics grid showing customers, LTV, retention rate
- Bottlenecks section with stage, duration, and delay rates
- Top refunded products with refund rates and counts
- Full dark mode support with Tailwind CSS

### Integration
- Added "Indsigt" tab to home.vue dashboard
- Created API proxy endpoint at `/api/insights_dashboard`
- Lazy loading when tab is selected

## Key Decisions

1. **Severity Classification Thresholds:**
   - Revenue leaks: high >10%, medium >5%, low otherwise
   - Bottlenecks: high >30% delay rate, medium >15%
   - Refunds: high >15% rate, medium >8%

2. **Recommendation Generation:**
   - Priority 1 = highest priority (most urgent action)
   - Categories: revenue, operations, retention, products
   - Each recommendation includes potential impact (high/medium/low)

3. **No Data Fallback:**
   - Empty state message when no orders exist
   - Placeholder recommendation to connect store

## Files Changed

```
backend/src/endpoints/insights_dashboard.py   (new)
backend/src/endpoints/getData.py                (modified)
frontend/components/charts/InsightsDashboard.vue (new)
frontend/server/api/insights_dashboard.get.ts   (new)
frontend/pages/home.vue                        (modified)
```

## Verification

- Backend endpoint returns aggregated insights from database
- Frontend dashboard displays all insight categories with proper styling
- Tab navigation works correctly with InsightsDashboard component
- Dark mode support functional with Tailwind dark: variants

## Self-Check

- [x] Created files exist
- [x] Commit hash verified
- [x] All imports properly configured
- [x] Dark mode support implemented
- [x] API proxy endpoint created