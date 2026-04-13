# Codebase Concerns

**Analysis Date:** 2026-04-13

## Tech Debt

**No formal test suite:**
- Frontend has no Vitest/Playwright tests
- Backend has no pytest tests
- Risk: Regression-prone changes
- Fix approach: Add Vitest for frontend, pytest for backend

**No linting/formatting configured:**
- Frontend: No ESLint/Prettier
- Backend: No flake8/isort
- Risk: Inconsistent code style
- Fix approach: Add ESLint + Prettier (frontend), flake8 + black (backend)

**Duplicate auth logic:**
- `get_current_user()` duplicated in multiple backend files:
  - `src/endpoints/getData.py`
  - `src/endpoints/auth.py`
  - `src/endpoints/customerAnalytics.py`
- Fix approach: Create shared auth module

**JWT validation inconsistent:**
- Frontend server routes validate JWT themselves via `middleware/require-auth.ts`
- But login route creates JWT without proper validation of incoming credentials against API response
- Fix approach: Centralize auth validation

## Known Bugs

**Frontend/Backend integration issues:**
- Multiple places where API response structure assumptions may differ
- Example: `home.vue` has complex fallback logic for analytics data structure
- Files: `frontend/pages/home.vue`, line 311

**Demo user auto-creation:**
- Special-case handling in login flow (`_handle_demo_login`)
- May have edge cases around demo data generation
- Files: `backend/src/endpoints/getData.py`, lines 413-490

## Security Considerations

**Password handling:**
- Bcrypt truncation at 72 characters (handled in code, line 392)
- Need to ensure migration script has run for all users
- Files: `backend/src/endpoints/getData.py`

**JWT secret:**
- Must be set via environment variable
- No validation at startup if missing (will fail at runtime)
- Files: `backend/src/endpoints/getData.py`

**SQL injection protection:**
- Uses parameterized queries via SQLAlchemy `text()`
- Good pattern, ensure it's followed consistently

## Performance Bottlenecks

**Database connection management:**
- Global `conn` object in `getData.py` - single connection
- May not handle high concurrency well
- Files: `backend/src/endpoints/getData.py`
- Fix approach: Use connection pooling properly

**ML model training:**
- `predictSales.py` runs synchronously during data pipeline
- Could be moved to background task (Celery)
- Files: `backend/src/scripts/analysis/predictSales.py`

**Large dataframes in memory:**
- Uses pandas loaded entirely into memory
- Could cause issues with large datasets
- Files: `backend/src/scripts/db/populateDB.py`

## Fragile Areas

**OAuth callbacks:**
- Shopify OAuth flow depends on state validation
- Multiple error cases to handle
- Files: `frontend/server/api/integrations/shopify/*`, `backend/src/endpoints/shopify.py`

**Environment configuration:**
- Many required env vars without validation
- App fails silently or crashes at runtime if missing
- Files: `backend/src/endpoints/getData.py` (initialize_app function)

## Scaling Limits

**Database:**
- MySQL single instance, no read replicas in config
- Connection pooling may need tuning

**Frontend:**
- Nuxt SSR requires Node.js server
- Could add CDN for static assets in production

## Dependencies at Risk

**Older packages:**
- bcrypt==4.0.1 (pinned exact version)
- Some packages may have security vulnerabilities

**Shopify API:**
- @shopify/shopify-api 11.8.0 - may need updates

## Missing Critical Features

**Error monitoring:**
- No Sentry or similar error tracking
- Production issues difficult to diagnose

**API documentation:**
- Backend has FastAPI auto-docs at `/docs` (Swagger UI)
- No OpenAPI spec for frontend

## Test Coverage Gaps

**All endpoints:**
- No unit or integration tests
- Risk: API changes break functionality undetected
- Priority: High

**Authentication flow:**
- No tests for login/register/logout
- Risk: Auth regression breaks all users
- Priority: High

**Data processing:**
- No tests for `populateDB.py`, `predictSales.py`
- Risk: Data pipeline failures
- Priority: Medium

---

*Concerns audit: 2026-04-13*