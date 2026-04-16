---
phase: 99-shopify-test-data
plan: "01"
subsystem: backend
tags: [shopify, test-data, danish-golf]
dependency_graph:
  requires: []
  provides:
    - generateTestData.py
  affects: [main.py]
tech_stack:
  - Python
  - Shopify Admin REST API
key_files:
  created:
    - backend/src/scripts/generateTestData.py
decisions:
  - D-01: Generate products first, then orders use those products
  - D-02: All 6 categories: golf clubs, golf bags, golf balls, gloves, golf apparel, accessories
  - D-03: Customer data in Danish (names, addresses, cities)
  - D-04: Order values between 500-5000 DKK
metrics:
  duration_sec: 180
  completed_date: "2026-04-16"
---

# Phase 99 Plan 01: Shopify Test Data Generator - Summary

## One-Liner

Danish golf test data generation module with CLI for products, orders, and customers

## Completed Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Create test data generation module | 75b7405 |

## Key Changes

- Created `backend/src/scripts/generateTestData.py`
- Imports from shopify.py: constants, create_product, access token
- Generates Danish customer data with random names, addresses, cities
- Generates 6 categories: golf clubs, golf bags, golf balls, gloves, golf apparel, accessories
- Generates orders with random 1-3 products, total 500-5000 DKK
- CLI with `--products`, `--orders`, `--customers`, `--dry-run` flags
- Uses credentials from os.getenv: SHOPIFY_SHOP, SHOPIFY_ACCESS_TOKEN

## CLI Usage

```bash
# Generate test data
uv run python src/scripts/generateTestData.py --products 20 --orders 10

# Dry run to preview
uv run python src/scripts/generateTestData.py --dry-run
```

## Implementation Details

### Danish Customer Generation
- Uses DANISH_FIRST_NAMES, DANISH_LAST_NAMES from shopify.py
- Generates random addresses with Danish cities and zip codes
- Email format: `firstname.lastnameN@golfmail.dk`

### Product Categories
- golf clubs: Driver, Iron Set, Putter, Wedge, Hybrid
- golf bags: Stand Bag, Cart Bag, Travel Bag
- golf balls: Tour Pro, Practice, Premium
- gloves: Herre, Dame, Junior
- golf apparel: Cap, Sko, Trøje, Vest, Regnjakke
- accessories: Håndklæde, Scorekort-holder, Divot, Tee-box

### Order Generation
- Random 1-3 products per order
- Order total: 500-5000 DKK
- Uses Shopify REST API for order creation
- Includes transaction for "paid" status

## Verification

- Module loads successfully: ✓
- CLI accepts --products, --orders, --customers arguments: ✓
- Dry-run shows sample data: ✓

## Deviations from Plan

None - plan executed exactly as written.

---