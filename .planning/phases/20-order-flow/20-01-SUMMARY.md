---
phase: 20-order-flow
plan: "01"
subsystem: Backend Pipeline
tags: [shopify, fulfillment, order-flow, analytics]
dependency_graph:
  requires: []
  provides: [order-flow-analysis]
  affects: [frontend-dashboard]
tech_stack:
  - FastAPI (Python)
  - Shopify GraphQL API
  - pandas
patterns:
  - GraphQL query extension
  - Duration calculation from timestamps
  - Percentile computation
key_files:
  created:
    - backend/src/endpoints/order_flow_analysis.py
  modified:
    - backend/src/integrations/shopify/shopify.py
    - backend/src/endpoints/getData.py
decisions:
  - Used pandas for duration calculations (consistent with existing codebase)
  - Registered endpoint at /api/order_flow_analysis route
  - Included tracking_company/carrier extraction for carrier analytics
metrics:
  duration_minutes: 15
  completed_date: "2026-04-17"
---

# Phase 20 Plan 01: Order Flow Analysis - Summary

## Objective

Extend Shopify order fetching to include fulfillment lifecycle data and create analysis API endpoint. This enables order flow analysis by capturing full lifecycle stages (created → processed → fulfilled → closed).

## Key Truths Verified

- Orders fetched from Shopify include fulfillment timestamps
- Orders include tracking details (carrier, tracking number)
- Shipping address and method are captured
- API endpoint returns computed stage durations

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extend get_orders() GraphQL query | 318d390 | shopify.py |
| 2 | Add order flow analysis API endpoint | 1b8c8e3 | order_flow_analysis.py |
| 3 | Register endpoint in FastAPI app | 1b8c8e3 | getData.py |

## Implementation Details

### Task 1: Extend get_orders() (Previously Completed)

Extended `backend/src/integrations/shopify/shopify.py` with:

**GraphQL Fields Added:**
- `processedAt`, `cancelledAt`, `closedAt` (order timestamps)
- `displayFulfillmentStatus` (fulfillment status)
- `shippingAddress { firstName, lastName, address1, city, zip, countryCode }`
- `shippingLines { title, priceSet }`
- `fulfillments { status, createdAt, trackingInfo { company, number, url } }`

**DataFrame Columns Added:**
- `processed_at`, `cancelled_at`, `closed_at`
- `fulfillment_status`, `fulfillment_created_at`
- `tracking_company`, `tracking_number`, `tracking_url`
- `shipping_first_name`, `shipping_last_name`, `shipping_address1`, `shipping_city`, `shipping_zip`, `shipping_country`

### Task 2: Create Order Flow Analysis Endpoint

Created `backend/src/endpoints/order_flow_analysis.py`:

**Endpoint:** `GET /api/order_flow_analysis`

**Features:**
- Optional date range filtering (start_date, end_date ISO 8601)
- Loads orders with fulfillment data from database
- Computes stage durations in hours/days:
  - `created_to_processed` (payment capture time)
  - `processed_to_fulfilled` (fulfillment/shipping time)
  - `fulfilled_to_closed` (closure time)
- Returns percentiles: median, P95, P99
- Calculates bottleneck percentages (>24h for created→processed, >48h for processed→fulfilled)
- Calculates fulfillment rate (% orders with tracking)
- Extracts top carriers from tracking_company
- Returns stage chart data for frontend visualization

**Response Structure:**
```json
{
  "order_count": 100,
  "stage_durations": {
    "created_to_processed": {"median_hours": 2.5, "p95_hours": 12.0, "p99_hours": 24.0},
    "processed_to_fulfilled": {"median_hours": 4.0, "p95_hours": 48.0, "p99_hours": 72.0},
    "fulfilled_to_closed": {"median_days": 3.0, "p95_days": 7.0, "p99_days": 14.0}
  },
  "bottlenecks": {
    "created_to_processed_exceeds_24h_pct": 5.0,
    "processed_to_fulfilled_exceeds_48h_pct": 3.0
  },
  "fulfillment_rate": 95.5,
  "top_carriers": [{"carrier": "GLS", "count": 45}, {"carrier": "PostNord", "count": 30}],
  "stage_chart_data": [...]
}
```

### Task 3: Register Endpoint

Modified `backend/src/endpoints/getData.py`:
- Imported `order_flow_analysis` router
- Registered at `/api` prefix with `Order Flow Analysis` tag
- Initialized globals (conn, JWT_SECRET, JWT_ALGORITHM) for the module

## Deviation Documentation

### Auto-fixed Issues

**None** - Plan executed exactly as designed.

## Auth Gates

**None** - No authentication gates encountered during execution.

## Known Stubs

**None** - All fields are wired to real data sources.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| none | - | No new security surface introduced |

## Self-Check

- [x] `order_flow_analysis.py` created
- [x] `getData.py` imports and includes order_flow_router
- [x] Syntax verified with py_compile
- [x] Commits verified: 318d390 (Task 1), 1b8c8e3 (Tasks 2-3)

## Self-Check: PASSED

---

**Plan Status:** Complete  
**Tasks:** 3/3 complete  
**Duration:** 15 minutes