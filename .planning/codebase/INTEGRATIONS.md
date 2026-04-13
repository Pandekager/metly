# External Integrations

**Analysis Date:** 2026-04-13

## APIs & External Services

**E-commerce Platforms:**

- **Shopify** - E-commerce platform integration
  - SDK/Client: `@shopify/shopify-api` 11.8.0
  - Auth: OAuth2 with access token storage
  - Endpoints: Products, Orders, Customers
  - Location: `backend/src/integrations/shopify/shopify.py`

- **Dandomain Modern** - Danish e-commerce platform
  - API Type: GraphQL
  - Auth: OAuth2
  - Location: `backend/src/integrations/dandomain/modern.py`

- **Dandomain Classic** - Danish e-commerce platform (legacy)
  - API Type: REST
  - Auth: Basic authentication
  - Location: `backend/src/integrations/dandomain/classic.py`

- **Demo** - Synthetic data for testing
  - Location: `backend/src/integrations/demo/demo.py`
  - Generates: Customers, orders, products, forecasts

**AI Services:**

- **Google Gemini** - AI business advice generation
  - API Key: GEMINI_API_KEY env var
  - Used by: `src/scripts/analysis/consultAi.py`

## Data Storage

**Databases:**
- **MySQL** (metlydk_main)
  - Connection: via SQLAlchemy + PyMySQL
  - Location: `backend/src/scripts/db/connections.py`
  - Tables: users, platforms, customers, orders, products, forecasts, ai_responses

**File Storage:**
- Local filesystem
  - Plots: `backend/plots/` directory
  - Data: `backend/data/` directory

**Caching:**
- Redis (optional, via Celery)
  - Version: 7.1.x
  - Used for: Background task queue

## Authentication & Identity

**Auth Provider:**
- Custom JWT implementation
  - Token: JWT with HS256 algorithm
  - Expiry: 24 hours (60*60*24 seconds)
  - Storage: httpOnly cookie (frontend), JWT_SECRET env var (signing)
  - Validation: python-jose on backend, jsonwebtoken on frontend

## Monitoring & Observability

**Logging:**
- Python `logging` module
- Output: Console/standard output
- Structured messages with context

**Error Tracking:**
- None configured (per AGENTS.md)

## CI/CD & Deployment

**Hosting:**
- Development: Local (127.0.0.1:3000 frontend, 127.0.0.1:8000 backend)
- Production: Not specified in codebase

**CI Pipeline:**
- None configured in repository

## Environment Configuration

**Required env vars (backend):**
- DB_USR - Database username
- DB_PWD - Database password
- DB_USR_ADMIN - Admin database username
- DB_PWD_ADMIN - Admin database password
- JWT_SECRET - JWT signing secret
- JWT_ALGORITHM - JWT algorithm (default: HS256)
- GEMINI_API_KEY - Google AI API key

**Required env vars (frontend):**
- JWT_SECRET - For signing tokens on login
- API_BASE - Backend URL (default: http://127.0.0.1:8000/api)
- NUXT_DEV_TUNNEL_URL - Optional dev tunnel
- DEV_TUNNEL_URL - Optional dev tunnel

**Secrets location:**
- `backend/.env` - Local development secrets
- `frontend/.env` - Local development secrets
- Not committed to repository

## Webhooks & Callbacks

**Incoming:**
- Shopify OAuth callback: `/api/integrations/shopify/callback.get.ts`

**Outgoing:**
- None configured

---

*Integration audit: 2026-04-13*