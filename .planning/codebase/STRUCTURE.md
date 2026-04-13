# Codebase Structure

**Analysis Date:** 2026-04-13

## Directory Layout

```
metly/
├── frontend/                    # Nuxt 4 application (Bun)
├── backend/                     # FastAPI application (Poetry)
├── .planning/                   # GSD planning docs
├── dev-frontend.sh             # Frontend dev script
├── dev-backend.sh              # Backend dev script
└── AGENTS.md                   # Project guidelines
```

## Frontend Structure

```
frontend/
├── nuxt.config.ts              # Nuxt configuration
├── package.json                # Bun package manifest
├── tsconfig.json               # TypeScript config
├── tailwind.config.js          # Tailwind CSS config
├── app.vue                     # Root Vue component
├── pages/                      # Route pages
│   ├── index.vue               # Landing page
│   ├── login.vue               # Login page
│   ├── signup.vue              # Signup page
│   ├── home.vue                # Dashboard
│   ├── privacy.vue             # Privacy policy
│   ├── security.vue            # Security page
│   └── data-processing.vue     # Data processing info
├── components/                  # Vue components
│   ├── Navbar.vue              # Navigation bar
│   ├── Footer.vue             # Footer
│   ├── ThemeToggle.vue        # Theme switcher
│   ├── LegalDocumentModal.vue # Legal modal
│   ├── AIBusinessAdvice.vue    # AI advice display
│   ├── charts/                # Chart components
│   │   ├── ForecastChart.vue
│   │   ├── CustomerAnalyticsChart.vue
│   │   ├── CityRevenueChart.vue
│   │   ├── CityBarChart.vue
│   │   └── DemoChart.vue
│   ├── maps/                  # Map components
│   │   └── CustomerMap.vue
│   └── sections/               # Page sections
│       ├── HeroSection.vue
│       ├── AboutSection.vue
│       ├── FeaturesSection.vue
│       └── ContactSection.vue
├── server/                      # Nuxt server routes (API proxy)
│   └── api/
│       ├── auth/
│       │   ├── login.post.ts
│       │   ├── register.post.ts
│       │   ├── logout.post.ts
│       │   ├── check.get.ts
│       │   ├── account.delete.ts
│       │   └── onboarding-status.get.ts
│       ├── forecasts.get.ts
│       ├── customer_analytics.get.ts
│       ├── forecast_business_advice.get.ts
│       └── integrations/shopify/
│           ├── install.get.ts
│           ├── callback.get.ts
│           └── status.get.ts
├── stores/                      # Pinia stores
│   └── auth.ts                 # Auth state
├── composables/                 # Vue composables
│   ├── useTheme.ts
│   └── useLegalDocuments.ts
├── types/                       # TypeScript types
│   ├── auth.ts
│   ├── login.ts
│   ├── forecast.ts
│   ├── forecast-business-advice.ts
│   └── api.ts
├── utils/                       # Utility functions
│   ├── colors.ts
│   └── text-classes.ts
├── middleware/                  # Nuxt middleware
│   └── require-auth.ts         # Auth guard
├── assets/
│   └── css/
│       └── main.css            # Global CSS
└── public/                     # Static assets
```

## Backend Structure

```
backend/
├── main.py                     # Orchestration script
├── pyproject.toml             # Poetry manifest
├── src/
│   ├── endpoints/              # FastAPI routes
│   │   ├── getData.py         # Main app (login, register, forecasts)
│   │   ├── auth.py            # Auth utilities
│   │   ├── customerAnalytics.py  # Customer analytics
│   │   └── shopify.py         # Shopify integration
│   ├── scripts/               # Core scripts
│   │   ├── db/                # Database operations
│   │   │   ├── connections.py     # DB connection
│   │   │   ├── createDB.py        # Create tables
│   │   │   ├── populateDB.py      # Fetch & store data
│   │   │   ├── enforceDataProtection.py  # GDPR retention
│   │   │   └── populateDemoCustomers.py # Demo data
│   │   └── analysis/          # Analysis scripts
│   │       ├── predictSales.py    # ML forecasting
│   │       ├── consultAi.py       # AI business advice
│   │       ├── customers.py       # Customer analysis
│   │       ├── orders.py         # Order analysis
│   │       └── products.py       # Product analysis
│   ├── integrations/          # E-commerce integrations
│   │   ├── shopify/
│   │   │   └── shopify.py     # Shopify API client
│   │   ├── dandomain/
│   │   │   ├── modern.py     # Dandomain GraphQL
│   │   │   └── classic.py     # Dandomain REST
│   │   └── demo/
│   │       └── demo.py        # Demo data generator
│   └── db/
│       └── createTables.sql   # SQL schema
├── scripts/                   # Utility scripts
│   ├── generate_jwt.py        # JWT generation
│   └── migrate_passwords.py   # Password migration
├── data/                      # Static data files
├── plots/                     # Generated plots
└── find_customer_tables.py    # Utility scripts
```

## Key File Locations

**Entry Points:**
- `frontend/nuxt.config.ts`: Frontend app entry
- `backend/src/endpoints/getData.py`: Backend API entry
- `backend/main.py`: Data pipeline orchestration

**Configuration:**
- `frontend/nuxt.config.ts`: Nuxt config (runtime config, modules, app head)
- `frontend/tailwind.config.js`: Tailwind theme
- `backend/pyproject.toml`: Python dependencies
- `backend/.env`: Environment variables (DB credentials, JWT secret, API keys)

**Core Logic:**
- `frontend/pages/home.vue`: Dashboard page with charts and maps
- `frontend/stores/auth.ts`: Auth state management
- `backend/src/endpoints/getData.py`: Main API with auth and forecasts
- `backend/src/scripts/analysis/predictSales.py`: ML sales forecasting

**Testing:**
- No formal test framework configured (per AGENTS.md)

## Naming Conventions

**Files:**
- Vue components: PascalCase (e.g., `ForecastChart.vue`)
- Server routes: kebab-case with method prefix (e.g., `login.post.ts`)
- Python modules: snake_case (e.g., `predictSales.py`)
- TypeScript types: PascalCase (e.g., `Forecast.ts`)

**Directories:**
- Vue: PascalCase or kebab-case (`components/charts/`, `server/api/`)
- Python: snake_case (`scripts/db/`, `integrations/shopify/`)

## Where to Add New Code

**New Frontend Feature:**
- UI logic: `components/` or `pages/`
- API proxy: `server/api/`
- State: `stores/`
- Types: `types/`

**New Backend Endpoint:**
- Route handler: `src/endpoints/`
- DB operations: `src/scripts/db/`
- External integration: `src/integrations/`

**New Analysis Script:**
- ML/AI: `src/scripts/analysis/`
- Data fetching: `src/scripts/db/`

---

*Structure analysis: 2026-04-13*