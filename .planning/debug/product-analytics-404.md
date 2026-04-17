---
status: awaiting_human_verify
trigger: "product-analytics-404: GET /api/product_analytics returns 404 via ngrok"
created: 2026-04-16T00:00:00Z
updated: 2026-04-16T00:00:00Z
---

## Current Focus
hypothesis: "Fixed - created missing server proxy routes"
test: "Build completed successfully with new routes"
expecting: "Routes /api/product_analytics and /api/product_business_advice will now proxy to backend"
next_action: "User needs to verify via ngrok URL"

## Symptoms
expected: Product analytics data should be returned for the demo user
actual: GET request to /api/product_analytics returns 404 via ngrok
errors: "Failed to fetch product analytics: FetchError: [GET] "/api/product_analytics": 404"
reproduction: Navigate to Produkter tab in the frontend at the ngrok URL
started: Started after recent changes to shopify-dev.sh script

## Eliminated
- hypothesis: "Ngrok proxy issue" - No proxy needed between frontend and backend, both on localhost
- hypothesis: "Backend endpoint not registered" - Backend has the endpoints registered correctly
- hypothesis: "nuxt.config.ts proxy configuration missing" - Not needed, using server routes instead

## Evidence
- timestamp: 2026-04-16
  checked: "nuxt.config.ts proxy configuration"
  found: "No proxy configuration exists for /api/* routes"
  implication: "Direct client fetches to /api/* need server-side routes to proxy"

- timestamp: 2026-04-16
  checked: "Server API routes directory"
  found: "customer_analytics.get.ts exists, but product_analytics.get.ts does NOT"
  implication: "product_analytics was missing its server proxy route"

- timestamp: 2026-04-16
  checked: "Backend endpoint registration"
  found: "Backend has both product_analytics and product_business_advice endpoints registered"
  implication: "Backend endpoints work, just needed server-side proxy"

- timestamp: 2026-04-16
  checked: "Frontend build output"
  found: "product_analytics.get.mjs and product_business_advice.get.mjs now compiled successfully"
  implication: "Fix is correctly implemented and build passes"

## Resolution
root_cause: "The frontend's home.vue calls /api/product_analytics and /api/product_business_advice directly from the browser. Nuxt requires either: (1) server-side proxy routes in /server/api/, or (2) a nitro proxy configuration. Customer analytics worked because it had a server route. Product analytics was missing this."
fix: "Created two new server-side proxy routes: /server/api/product_analytics.get.ts and /server/api/product_business_advice.get.ts that proxy requests to the backend using runtimeConfig.public.apiBase"
verification: "User needs to test via ngrok URL: Navigate to Produkter tab and verify data loads"
files_changed:
  - "frontend/server/api/product_analytics.get.ts"
  - "frontend/server/api/product_business_advice.get.ts"
