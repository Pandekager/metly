---
status: complete
phase: 31-ui-enhancements
source:
  - 31-01-SUMMARY.md
  - 31-02-SUMMARY.md
started: "2026-04-27T11:28:00Z"
updated: "2026-04-27T11:31:00Z"
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Info Icons on Dashboard Tabs
expected: |
  Each of the 10 dashboard tabs (Ordrer, Ordre flow, Kunder, Produkter, Indtægtslækage, Returner, Checkout, Flaskehalse, Kundeadfærd, Indsigt) displays an info icon. Clicking the icon shows a tooltip explaining what that tab shows and how to interpret the data.
result: pass

### 2. Tooltip Interaction
expected: |
  Clicking an info icon opens its tooltip. Clicking outside the tooltip or pressing Escape closes it. Tooltips have smooth show/hide transitions.
result: pass

### 3. Date Range Picker UI
expected: |
  Above the tab selection bar, there is a date range picker with "Fra:" (From) and "Til:" (To) date inputs, plus a "Nulstil" (Reset) button.
result: pass

### 4. Date Range Filtering
expected: |
  Selecting a date range and clicking a non-Forecast tab (e.g., Ordre flow, Kunder) filters the chart data to that range. The API receives start_date and end_date query parameters.
result: pass

### 5. Forecast Tab Ignores Date Range
expected: |
  The Forecast tab (Ordrer) always displays current month + next month data, regardless of the date range picker selection.
result: pass

### 6. Reset Button
expected: |
  Clicking "Nulstil" resets the date range to the current month.
result: pass

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]