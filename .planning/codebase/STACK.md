# Technology Stack

**Analysis Date:** 2026-04-13

## Languages

**Primary:**
- TypeScript - Frontend (Nuxt 4, Vue 3)
- Python - Backend (FastAPI, data processing)

**Secondary:**
- Vue (HTML templates in .vue files)
- SQL (database queries)

## Runtime

**Environment:**
- Bun 1.3.11 - Frontend package manager and dev server
- Python 3.11+ - Backend runtime
- Node.js - Used internally by some packages

**Package Manager:**
- Frontend: Bun (packageManager: bun@1.3.11 in package.json)
- Backend: Poetry (pyproject.toml)

## Frameworks

**Core:**
- Nuxt 4.2.2 - Vue 3 meta-framework with SSR
- FastAPI 0.123.x - Python web framework

**Frontend Modules:**
- @pinia/nuxt 0.11.3 - State management
- @nuxtjs/tailwindcss 6.14.0 - CSS framework
- @nuxtjs/google-fonts 3.2.0 - Font loading
- @nuxt/image 2.0.0 - Image optimization

**Data Visualization:**
- chart.js 4.5.1 - Chart library
- vue-chartjs 5.3.3 - Chart.js Vue wrapper
- leaflet 1.9.4 - Maps
- @vue-leaflet/vue-leaflet 0.10.1 - Leaflet Vue wrapper

**Backend Frameworks:**
- SQLAlchemy 2.0.x - ORM and SQL
- Pydantic 2.12.x - Data validation
- Alembic 1.17.x - Database migrations

**ML/Analysis:**
- pandas 2.3.x - Data manipulation
- scikit-learn 1.7.x - Machine learning
- lightgbm 4.5.x - Gradient boosting
- seaborn 0.13.x - Statistical visualization

**Task Queue:**
- Celery 5.6.x - Background tasks
- Redis 7.1.x - Message broker

**Testing:**
- No formal test framework configured

**Build/Dev:**
- uvicorn 0.38.x - ASGI server
- Vite - Frontend bundler (via Nuxt)

## Key Dependencies

**Critical:**
- fastapi - API framework
- sqlalchemy - Database ORM
- pandas - Data processing
- lightgbm / scikit-learn - ML forecasting
- nuxt - Frontend framework

**Authentication:**
- jsonwebtoken - Frontend JWT handling
- python-jose - Backend JWT validation
- passlib + bcrypt - Password hashing

**External APIs:**
- @shopify/shopify-api 11.8.0 - Shopify integration
- httpx 0.28.x - HTTP client
- requests 2.33.x - HTTP client

**CMS/E-commerce:**
- Custom integrations for Dandomain (GraphQL + REST)
- Demo integration (synthetic data)

## Configuration

**Environment:**
- Frontend: `runtimeConfig` in nuxt.config.ts
- Backend: `.env` file loaded via python-dotenv
- Key vars: DB_USR, DB_PWD, JWT_SECRET, API keys

**Build:**
- Frontend: Nuxt build (Vite)
- Backend: Hatch build (wheel packages)

## Platform Requirements

**Development:**
- Bun for frontend package management
- Poetry for Python dependencies
- MySQL database
- Node.js (for Vite/build tooling)

**Production:**
- MySQL database (metlydk_main)
- Redis for Celery (if used)
- Python 3.11+ server

---

*Stack analysis: 2026-04-13*