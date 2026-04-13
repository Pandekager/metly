# Architecture

**Analysis Date:** 2026-04-13

## Pattern Overview

**Overall:** Split-stack with Nuxt proxy architecture

**Key Characteristics:**
- Frontend (Nuxt 4) acts as proxy to backend FastAPI
- Frontend server routes (`server/api/*`) forward to backend at `http://127.0.0.1:8000`
- JWT authentication with httpOnly cookies
- Multi-tenant database isolation via `user_id` column
- Read-only external API integrations

## Layers

**Frontend (Nuxt 4 with Bun):**
- Location: `frontend/`
- Contains: Vue 3 components, pages, server routes, Pinia stores
- Dependencies: `@pinia/nuxt`, `@nuxtjs/tailwindcss`, `chart.js`, `vue-chartjs`, `leaflet`
- Serves: UI, authentication flow, data visualization

**Backend (FastAPI with Poetry):**
- Location: `backend/`
- Contains: API endpoints, database scripts, ML analysis, e-commerce integrations
- Dependencies: `fastapi`, `sqlalchemy`, `pandas`, `scikit-learn`, `lightgbm`
- Serves: Data processing, forecasting, AI business advice

**Database:**
- MySQL database (`metlydk_main`)
- Tables: users, platforms, customers, orders, products, forecasts, ai_responses
- Multi-tenant: Every table has `user_id` column

**External Integrations:**
- Shopify (OAuth2, REST API)
- Dandomain (Modern: GraphQL, Classic: REST)
- Demo (synthetic data generation)

## Data Flow

**Authentication Flow:**
1. User submits credentials to `frontend/server/api/auth/login.post.ts`
2. Nuxt server routes request to FastAPI `/auth/login` endpoint
3. FastAPI validates against MySQL database, returns `user_id`
4. Nuxt server generates JWT signed with `JWT_SECRET`
5. JWT stored in httpOnly cookie for subsequent requests

**Dashboard Data Flow:**
1. User navigates to `/home` (requires auth middleware)
2. Page calls `/api/forecasts`, `/api/customer_analytics`, `/api/forecast_business_advice`
3. Nuxt server routes forward to FastAPI endpoints
4. FastAPI validates JWT, queries MySQL with `user_id` filter
5. Data returned to frontend for visualization (charts, maps)

**Onboarding Flow:**
1. User registers via `/auth/register` with platform selection
2. Backend creates user, assigns platform_id
3. Frontend polls `/auth/onboarding-status` for progress
4. Background: `main.py` orchestrates data fetching and analysis

## Key Abstractions

**Frontend Server Routes:**
- `server/api/auth/*` - Authentication proxy to backend
- `server/api/forecasts.get.ts` - Proxies `/forecasts` endpoint
- `server/api/customer_analytics.get.ts` - Proxies `/customer_analytics`
- `server/api/integrations/shopify/*` - Shopify OAuth flow

**Backend Endpoints:**
- `src/endpoints/getData.py` - Main app with login, register, forecasts, onboarding
- `src/endpoints/customerAnalytics.py` - City-level customer analytics
- `src/endpoints/shopify.py` - Shopify integration endpoints

**Scripts:**
- `src/scripts/db/populateDB.py` - Fetch external data, populate database
- `src/scripts/analysis/predictSales.py` - ML forecasting with scikit-learn/lightgbm
- `src/scripts/analysis/consultAi.py` - AI business advice via Gemini

**Integrations:**
- `src/integrations/shopify/shopify.py` - Shopify API client
- `src/integrations/dandomain/modern.py` - Dandomain GraphQL client
- `src/integrations/dandomain/classic.py` - Dandomain REST client
- `src/integrations/demo/demo.py` - Demo data generation

## Entry Points

**Frontend:**
- Location: `frontend/nuxt.config.ts`
- Triggers: `bun run dev` or `bun run build`
- Responsibilities: SSR, routing, auth middleware, API proxy

**Backend:**
- Location: `src/endpoints/getData.py`
- Triggers: `uvicorn src.endpoints.getData:app --reload`
- Responsibilities: API endpoints, DB connection, JWT validation

**Orchestration:**
- Location: `backend/main.py`
- Triggers: `python main.py`
- Responsibilities: Create tables, populate DB, run analysis, generate advice

## Error Handling

**API Level:**
- FastAPI `HTTPException` with status codes 400/401/403/500
- Frontend uses `createError` for user-facing errors
- Generic error messages to prevent enumeration

**Database Level:**
- Parameterized queries to prevent SQL injection
- Try/except with logging for all DB operations
- Connection pooling via SQLAlchemy

**Authentication:**
- JWT validation on every protected endpoint
- User access validation (can't query other users' data)
- Demo user special handling (auto-creation)

## Cross-Cutting Concerns

**Logging:** Python `logging` module with structured messages
**Validation:** Pydantic models for request/response schemas
**Authentication:** JWT with bcrypt password hashing
**Environment:** `.env` files loaded via `python-dotenv`

---

*Architecture analysis: 2026-04-13*