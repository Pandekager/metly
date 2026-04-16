---
phase: 99-shopify-test-data
plan: "02"
subsystem: backend
tags: [shopify, test-data, cron, scheduled-jobs]
dependency_graph:
  requires:
    - 99-01
  provides:
    - main.py CLI integration
    - SCHEDULE.md
  affects: [populateDB]
tech_stack:
  - Python
  - Cron
key_files:
  created:
    - backend/SCHEDULE.md
  modified:
    - backend/main.py
decisions:
  - D-05: Run daily via cron (0 0 * * * at midnight)
  - D-06: Use existing Shopify credentials from .env
  - D-07: Integrate with populateDB flow for database sync
metrics:
  duration_sec: 120
  completed_date: "2026-04-16"
---

# Phase 99 Plan 02: Test Data Integration - Summary

## One-Liner

main.py CLI integration and cron documentation for scheduled test data generation

## Completed Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Integrate with main.py CLI | 75b7405 |
| 2 | Document cron setup | 75b7405 |

## Key Changes

- Updated `main.py` to add `--test-data` and `--user` flags
- Created `backend/SCHEDULE.md` with cron setup documentation
- Test data generation integrates with populateDB for database sync

## Changes Details

### main.py Updates
- Added argparse with `--test-data` and `--user` flags
- Added import for `run_test_generation` from generateTestData
- When `--test-data` flag set:
  1. Runs `run_test_generation(products_count=20, orders_count=10)`
  2. If `--user` provided, calls `populateDB(db_usr, db_pwd, user_ids=[user_id])`

### SCHEDULE.md
- Documents cron expression: `0 0 * * *` (midnight daily)
- Example crontab entry provided
- Environment variables documented (SHOPIFY_SHOP, SHOPIFY_ACCESS_TOKEN, etc.)
- Integration with populateDB flow documented

## Usage

```bash
# Generate test data only
uv run python main.py --test-data

# Generate and sync to database
uv run python main.py --test-data --user <USER_ID>
```

## Verification

- main.py --help shows --test-data flag: ✓
- CLI accepts --user argument: ✓
- SCHEDULE.md contains cron documentation: ✓

## Deviations from Plan

None - plan executed exactly as written.

---