---
phase: 20-order-flow
plan: 02
tags: [dashboard, charts, order-flow, vue-chartjs]
key_files:
  created:
    - frontend/components/charts/OrderFlowChart.vue
    - frontend/server/api/order_flow_analysis.get.ts
  modified:
    - frontend/pages/home.vue
dependency_graph:
  requires: [20-01]
  provides: [order-flow-chart-dashboard]
  affects: [home.vue]
tech_stack:
  - vue-chartjs (Bar component)
  - Chart.js (registered components)
  - Nuxt 3 useFetch (API calls)
  - useTheme (dark/light mode)
---

# Phase 20 Plan 02: Order Flow Chart Integration

## Summary

Created frontend visualization for order flow analysis using vue-chartjs Bar component, integrated into existing dashboard with "Ordre flow" tab. The chart displays average time in hours for each order lifecycle stage with red flag highlighting when thresholds are exceeded.

## Implementation Details

### OrderFlowChart Component
- Uses `Bar` component from vue-chartjs
- Displays stage durations: Oprettet → Behandlet, Behandlet → Afsendt, Afsendt → Lukket
- Red flag alerts when:
  - Created→Processed > 24h (Langsom behandling)
  - Processed→Fulfilled > 48h (Langsom levering)
- Danish labels throughout
- Uses `useTheme` for dark/light mode support (follows CityBarChart pattern)

### Frontend API Proxy
- Created `frontend/server/api/order_flow_analysis.get.ts`
- Proxies to backend `/api/order_flow_analysis`
- Uses JWT auth from cookie/header

### Dashboard Integration
- Added "Ordre flow" tab to home.vue dashboard
- Tab lazy loads data when selected (pattern from D-03)
- OrderFlowChart is rendered in tab content section

## Danish Translations

| English | Danish |
|---------|-------|
| Order flow | Ordre flow |
| Created → Processed | Oprettet → Behandlet |
| Processed → Fulfilled | Behandlet → Afsendt |
| Fulfilled → Closed | Afsendt → Lukket |
| Total orders | Samlet antal ordrer |
| Fulfillment rate | Opfyldelsesrate |
| Top carrier | Top carrier |
| Slow processing | Langsom behandling |
| Slow delivery | Langsom levering |
| Average time (hours) | Gennemsnitlig tid (timer) |

## Key Decisions

1. **Bar chart vs Line chart**: Chose Bar for stage duration comparison (horizontal discrete categories)
2. **Red flag threshold**: 10% of orders exceeding threshold triggers warning (not absolute value)
3. **Chart colors**: Red highlight for exceeding thresholds, indigo for normal (follows ProductAnalyticsChart pattern)

## Metrics

- Tasks completed: 3/3
- Commits: 2
- Duration: ~15 minutes

## Verification

After backend restart, verify:
- Frontend loads at http://127.0.0.1:3000
- Dashboard shows "Ordre flow" tab
- Chart renders with stage data from backend

## Self-Check: PASSED

- [x] OrderFlowChart.vue created with Bar chart
- [x] Chart displays stage durations in hours/days
- [x] Red flag alerts when thresholds exceeded
- [x] Danish labels throughout
- [x] Dark mode support via useTheme
- [x] Frontend API proxy created
- [x] "Ordre flow" tab added to home.vue dashboard
- [x] Lazy loading preserved (tab-based fetch, not on mount)

## Deviations from Plan

None - executed exactly as planned.