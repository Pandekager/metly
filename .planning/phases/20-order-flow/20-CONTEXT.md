# Phase 20: Order Flow Analysis - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Analyze the full lifecycle of each order from creation to fulfillment and completion. Identify delays between steps, highlight bottlenecks, and surface patterns where a small percentage of orders cause most delays. Present insights in plain language with clear business impact.

</domain>

<decisions>
## Implementation Decisions

### Data Source
- **D-01:** Use Shopify order data via GraphQL Admin API
- **D-02:** Track fields: created_at, processed_at, fulfilled_at, cancelled_at, closed_at

### Analysis Metrics
- **D-03:** Calculate time between each lifecycle stage
- **D-04:** Identify median and P95/P99 delay times
- **D-05:** Calculate percentage of orders exceeding threshold

### UI Display
- **D-06:** Simple bar-chart showing average time per stage
- **D-07:** Highlight "red flag" metrics that exceed thresholds
- **D-08:** Plain Danish language explanations

### Thresholds (to define during implementation)
- Acceptable delay times per stage
- What constitutes "bottleneck" status

### Agent's Discretion
- Specific chart library/approach
- Exact threshold values
- Detail level in explanations

</decisions>

<specifics>
## Specific Ideas

- Similar to existing ForecastChart pattern
- Reuse existing chart components
- Integrate with existing dashboard tab structure
</specifics>

<deferred>
## Deferred Ideas

None yet

</deferred>