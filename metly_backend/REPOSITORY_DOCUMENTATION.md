# Metly Backend Repository Documentation
**For AI Systems: Complete Repository Overview**

---

## Overview
Metly Backend is a Python FastAPI-based multi-tenant e-commerce integration platform that connects with DanDomain (Classic and Modern), supports demo data generation, performs sales forecasting using machine learning, and provides AI-powered business advice. The system is designed to be READ-ONLY - it never writes data to external e-commerce platforms.

**Tech Stack:**
- FastAPI (web framework)
- SQLAlchemy + PyMySQL (database ORM/driver)
- Pydantic (data validation)
- LightGBM (machine learning for sales forecasting)
- Google Gemini AI (business advice)
- pandas, numpy, scikit-learn (data analysis)

---

## Project Structure
```
/home/rasmus/Work/metly_backend/
├── main.py                      # Main entry point for batch operations
├── passenger_wsgi.py             # WSGI adapter for Passenger hosting
├── pyproject.toml               # Project configuration and dependencies
├── .env                         # Environment variables (credentials)
├── README.md                    # Quick start instructions
├── SECURITY_IMPROVEMENTS.md     # Security documentation
├── .github/copilot-instructions.md # GitHub Copilot instructions
├── .vscode/tasks.json           # VS Code task configuration
├── scripts/                     # Utility scripts
│   ├── generate_jwt.py          # JWT token generation
│   └── migrate_passwords.py    # Password hashing migration
└── src/                        # Main source code
    ├── endpoints/
    │   └── getData.py          # FastAPI REST API endpoints
    ├── db/
    │   ├── createTables.sql     # Database schema definition
    │   └── __init__.py        # Empty module marker
    ├── scripts/
    │   ├── db/
    │   │   ├── connections.py   # Incomplete connection helper
    │   │   ├── createDB.py     # DB initialization & user management
    │   │   └── populateDB.py   # Data fetching from integrations
    │   └── analysis/
    │       ├── __init__.py      # Empty module marker
    │       ├── customers.py     # Customer segmentation (incomplete)
    │       ├── orders.py        # Product co-occurrence analysis
    │       ├── products.py     # Product sales clustering (incomplete)
    │       ├── predictSales.py  # Sales forecasting with LightGBM
    │       └── consultAi.py    # AI business advice via Gemini
    └── integrations/
        ├── __init__.py         # Empty module marker
        ├── dandomain/
        │   ├── __init__.py    # Empty module marker
        │   ├── classic.py     # DanDomain Classic REST API
        │   └── modern.py     # DanDomain Modern GraphQL API
        └── demo/
            └── demo.py        # Demo data generation

```

---

## Root Directory Files

### main.py
**Purpose:** Main entry point for batch operations (ETL pipeline)

**Function:**
- Orchestrates 4 sequential operations:
  1. Creates database tables
  2. Fetches and refreshes data from integrations
  3. Runs sales prediction analysis
  4. Generates AI business advice

**Key Operations:**
- Loads environment variables from `.env`
- Uses admin database credentials
- Implements retry logic (max 3 attempts) for database operations
- Logs execution time for each step

**Dependencies:**
- `createTables()` from `src.scripts.db.createDB`
- `populateDB()` from `src.scripts.db.populateDB`
- `predictSales()` from `src.scripts.analysis.predictSales`
- `get_business_advice()` from `src.scripts.analysis.consultAi`

---

### passenger_wsgi.py
**Purpose:** WSGI adapter for Passenger (shared hosting deployment)

**Function:**
- Converts ASGI (FastAPI) application to WSGI for Passenger hosting
- Manages thread limits for numerical libraries (OpenBLAS, MKL, etc.)
- Handles request/response conversion between WSGI and ASGI formats
- Ensures Python path includes `src/` directory

**Key Classes:**
- `ASGItoWSGI`: Converts FastAPI ASGI app to WSGI interface

**Environment Variables:**
- Sets thread limits to prevent resource exhaustion on shared hosting

---

### pyproject.toml
**Purpose:** Project configuration and dependency management

**Dependencies:**
- FastAPI 0.123.x (web framework)
- Pydantic 2.x (data validation)
- SQLAlchemy 2.x (ORM)
- Alembic 1.17.x (migrations)
- structlog (structured logging)
- Celery + Redis (background tasks/queuing)
- Uvicorn (ASGI server)
- PyMySQL (MySQL driver)
- pandas, numpy, seaborn (data analysis)
- scikit-learn (machine learning)
- LightGBM 4.5.x (gradient boosting for forecasting)
- passlib + bcrypt (password hashing)
- python-jose (JWT tokens)
- email-validator (email validation)

---

### .env
**Purpose:** Environment configuration and credentials

**Variables:**
```
DB_USR=metlydk_app          # App database user
DB_PWD=Tr23VYOR4EK8e0u6H   # App database password
DB_USR_ADMIN=metlydk_rasmus  # Admin database user
DB_PWD_ADMIN=OAQl+]1I5b_9I+[ # Admin database password
JWT_SECRET=2xHund2LIFE      # JWT signing secret
JWT_ALGORITHM=HS256          # JWT algorithm
GEMINI_API_KEY=AIzaSy...    # Google Gemini AI API key
```

---

### README.md
**Purpose:** Quick start guide for developers

**Content:**
- Instructions for running the project via `run_main.sh`
- Virtual environment setup
- Troubleshooting tips
- Examples of running in background, logging to file

---

### SECURITY_IMPROVEMENTS.md
**Purpose:** Documentation for security enhancements

**Key Security Features:**
1. **Password Hashing:** bcrypt hashing for all passwords
2. **SQL Injection Prevention:** Parameterized queries via SQLAlchemy
3. **Email Validation:** Pydantic EmailStr validation
4. **Timing Attack Prevention:** Generic error messages

**Setup Instructions:**
- Install passlib[bcrypt]
- Run migration script for existing passwords
- API usage examples

---

### .github/copilot-instructions.md
**Purpose:** GitHub Copilot AI assistant instructions

**Key Points:**
- System is READ-ONLY (never writes to e-commerce platforms)
- Multi-tenant architecture
- Current status and features
- Development setup guidance

---

### .vscode/tasks.json
**Purpose:** VS Code task configuration

**Tasks:**
- "Start Development Server": Runs uvicorn with auto-reload

---

## Scripts Directory

### scripts/generate_jwt.py
**Purpose:** Generate test JWT tokens for authentication

**Function:**
- Generates HS256 JWT tokens for testing
- Supports custom secret, expiration, and subject (UUID)
- Falls back to minimal HMAC implementation if python-jose unavailable

**Usage:**
```bash
python scripts/generate_jwt.py --sub <UUID> --secret mysecret --exp 600
```

---

### scripts/migrate_passwords.py
**Purpose:** Migrate plaintext passwords to bcrypt hashes (one-time operation)

**Function:**
- Connects to database and fetches all users
- Identifies plaintext passwords (not starting with $2b$)
- Hashes passwords using bcrypt
- Updates database with hashed passwords
- Skips already hashed passwords

**Safety:**
- Requires confirmation before running
- Handles errors gracefully
- One-way operation (passwords cannot be recovered)

---

## src/endpoints Directory

### src/endpoints/getData.py
**Purpose:** FastAPI REST API application

**Endpoints:**

1. **POST /auth/login**
   - Authenticates users with email/password
   - Validates bcrypt password hashes
   - Returns user_id on success
   - Uses parameterized queries to prevent SQL injection

2. **GET /forecasts**
   - Returns sales forecasts for authenticated user
   - Query parameters: `user_id` (optional, defaults to current user)
   - Returns historical and forecasted sales by subcategory
   - Requires JWT Bearer token

3. **GET /forecast_business_advice**
   - Returns AI-generated business advice
   - Query parameters: `user_id` (optional)
   - Retrieves latest AI response from database
   - Requires JWT Bearer token

**Authentication:**
- JWT token validation via `get_current_user()` dependency
- Token must contain valid UUID in `sub` claim
- Users can only access their own data

**Security:**
- Password hashing with bcrypt (12-char truncation for bcrypt limit)
- Email validation with Pydantic EmailStr
- Generic error messages to prevent timing attacks
- SQL injection prevention via SQLAlchemy text() with named parameters

**Global State:**
- `conn`: Database connection (initialized at startup)
- `df_users`: User DataFrame for authorization
- `JWT_SECRET`, `JWT_ALGORITHM`: JWT configuration

---

## src/db Directory

### src/db/createTables.sql
**Purpose:** Database schema definition

**Tables:**

1. **customers**
   - Stores customer billing information
   - FK to users.id
   - Indexed on user_id

2. **languages**
   - Stores language/site information
   - FK to users.id
   - Indexed on user_id

3. **orders**
   - Stores order headers
   - FK to users.id
   - Indexed on user_id, createdAt

4. **products**
   - Stores product catalog (DanDomain Classic)
   - Includes subcategory and maincategory hierarchy
   - FK to users.id
   - Indexed on user_id

5. **product_categories**
   - Stores category hierarchy (DanDomain Modern)
   - Includes path for navigation
   - FK to users.id
   - Indexed on user_id

6. **order_lines**
   - Stores individual order items
   - Links to orders and products
   - Includes unit revenue, cost, stock info
   - FK to users.id
   - Indexed on user_id, order_id, product_id

7. **top_pairs**
   - Stores product co-occurrence analysis results
   - Tracks how often products are bought together
   - FK to users.id
   - Indexed on user_id

8. **forecasts**
   - Stores sales forecasts and historical data
   - Includes subcategory breakdown
   - is_forecast flag distinguishes actuals from predictions
   - FK to users.id
   - Unique constraint on (date, subcategory_name, user_id)

9. **ai_responses**
   - Stores AI-generated business advice
   - Categorized by ai_category_id (e.g., "forecast_business_advice")
   - FK to users.id
   - Indexed on user_id

**Character Set:** latin1 with Danish collation (latin1_danish_ci)

---

## src/scripts/db Directory

### src/scripts/db/connections.py
**Purpose:** Database connection helper (incomplete)

**Status:** Stub file - imports connectDB but doesn't define any functions

---

### src/scripts/db/createDB.py
**Purpose:** Database initialization and user management

**Functions:**

1. **authenticateDB(db_usr, db_pwd)**
   - Tests database connectivity
   - Logs success/failure

2. **createTables(db_usr, db_pwd)**
   - Executes createTables.sql script
   - Creates all tables if not exist

3. **gen_password(length=14)**
   - Generates secure random passwords
   - Ensures at least one uppercase, lowercase, and digit
   - Uses secrets module for cryptographic randomness

4. **createUser(db_usr, db_pwd, platform, email, api_key, tenant)**
   - Creates new user with bcrypt-hashed password
   - Generates random password and displays it
   - Inserts into users table with platform credentials
   - Prevents duplicate email creation

**Dependencies:**
- passlib for bcrypt hashing
- createTables.sql for schema

---

### src/scripts/db/populateDB.py
**Purpose:** Main ETL pipeline - fetches data from all integrations

**Functions:**

1. **connectDB(db_usr, db_pwd)**
   - Creates database connection (PyMySQL + SQLAlchemy)
   - Attaches SQLAlchemy engine for pandas queries
   - Fetches users with platform info
   - Implements retry logic (max 3 attempts)
   - Returns (conn, df_users)

2. **populateDB(db_usr, db_pwd)**
   - Main ETL orchestrator
   - Iterates through all users
   - Fetches data based on platform type:
     - **Dandomain Modern:** GraphQL API
     - **Dandomain Classic:** REST API
     - **demo:** Generates dummy golf equipment data
   - Deletes existing data (respecting FK constraints)
   - Inserts fresh data in chunks (1000 rows)
   - Commits per user

**Data Flow:**
```
For each user:
  ↓
Identify platform (Modern/Classic/demo)
  ↓
Fetch API token (if Modern)
  ↓
Call integration functions:
  - getOrders() → orders, customers, order_lines, languages
  - getProductCategories() → product_categories
  - getProducts() (Classic only) → products
  - makeDummyData() (demo only)
  ↓
Delete existing data (child→parent order)
  ↓
Insert new data (chunked)
  ↓
Commit
```

**Integration Functions Called:**
- `getDandomainToken()` - OAuth token
- `ModernGetOrders()` - GraphQL orders
- `getProductCategories()` - GraphQL categories
- `ClassicGetOrders()` - REST orders
- `ClassicGetProducts()` - REST products
- `makeDummyData()` - Demo generation

---

## src/scripts/analysis Directory

### src/scripts/analysis/customers.py
**Purpose:** Customer segmentation analysis (incomplete)

**Function:** `customerSegmentation(conn, df_users)`

**Features:**
- Aggregates customer data (items, revenue, orders)
- Currency conversion (DKK, EUR, SEK, NOK)
- Merges with name_gender data
- Groups by postal code
- Calculates average order value

**Status:** Incomplete - doesn't save results to database

---

### src/scripts/analysis/orders.py
**Purpose:** Product co-occurrence/market basket analysis

**Function:** `orderAnalysis(conn, df_users)`

**Algorithm:**
1. Creates binary product basket matrix (order × product)
2. Computes co-occurrence matrix: `basket.T @ basket`
3. Extracts upper triangle (avoids duplicates)
4. Finds top 25 product pairs by co-occurrence
5. Saves to top_pairs table

**Purpose:** Identify products frequently bought together for cross-selling

**SQL:**
- Filters out tariff products (TOLDTARIFNR, TOLLTARIFF)
- Cleans product titles (HTML tags, extra dashes)

---

### src/scripts/analysis/products.py
**Purpose:** Product sales clustering analysis (incomplete)

**Function:** `predictSales(conn, df_users)` (mismatched name)

**Features:**
- Aggregates sales by product and date
- Extracts time features (year, month, day)
- Creates circular encoding (sin/cos) for temporal wrap-around
- Normalizes year to 0-1 range
- KMeans clustering to derive product categories
- Silhouette score optimization for number of clusters

**Status:** Incomplete - doesn't save results or predict sales

---

### src/scripts/analysis/predictSales.py
**Purpose:** Sales forecasting using LightGBM with uncertainty estimation

**Function:** `predictSales(db_usr, db_pwd)`

**Key Features:**

1. **Data Preparation:**
   - Fetches order_lines with product and order info
   - Filters out tariff products
   - Cleans product titles
   - Aggregates by subcategory and date
   - Fills missing days with zeros

2. **Feature Engineering:**
   - Recent lags (1-90 days)
   - Seasonal lags (7, 14, 30, 90, 365 days)
   - Rolling statistics (mean, std for 7, 14, 30 days)
   - Calendar features (dayofweek, month, quarter, etc.)
   - Holiday indicators (Christmas, Easter, Black Friday)
   - Trend features (linear trend, squared)
   - Cyclical encoding (sin/cos for periodic features)

3. **Model Training (LightGBM):**
   - Bootstrap ensemble (15 models) for uncertainty
   - Adaptive iterations based on data sparsity:
     - >80% zeros: 50 iterations
     - 60-80% zeros: 75 iterations
     - <60% zeros: 100 iterations
   - Poisson sampling for low-volume categories

4. **Forecasting:**
   - Multi-step recursive forecast
   - Horizon: remaining days in current month + next month
   - Low-volume: median of ensemble, rounded to integer
   - High-volume: mean of ensemble

5. **Fallback (Insufficient Data):**
   - Linear trend extrapolation with uncertainty bounds
   - Or constant median for very sparse data
   - Ensures non-negative predictions

6. **Database Storage:**
   - Deletes existing forecasts from last year
   - Inserts historical + forecast data
   - Batch insert with transaction

**Helper Functions:**
- `_configure_logger()`: Structured logging adapter
- `calculate_mape()`: Mean Absolute Percentage Error
- `make_supervised()`: Feature engineering for time series
- `read_sql_with_retry()`: Robust SQL with reconnect

**Thread Limits:** Sets OpenBLAS, MKL, OMP, NUMEXPR to 1 thread

---

### src/scripts/analysis/consultAi.py
**Purpose:** Generate AI business advice using Google Gemini

**Functions:**

1. **get_business_advice(db_usr, db_pwd)**
   - Main orchestrator
   - Loops through all users
   - Fetches forecast data
   - Calls Gemini AI
   - Saves response to ai_responses table

2. **prepare_data_summary(df)**
   - Formats forecast data for AI prompt
   - Separates historical vs forecast
   - Summarizes by category
   - Creates structured markdown summary

3. **call_gemini_ai(data_summary, max_retries=3)**
   - Configures Gemini API (gemini-2.5-flash model)
   - Sends Danish-language prompt with data
   - Implements exponential backoff retries
   - Returns AI advice text

4. **save_ai_response(conn, user_id, response_text)**
   - Deletes existing responses for category
   - Inserts new AI response
   - Timestamped with current datetime

**Prompt Structure:**
- Role: Danish e-commerce expert
- Task: Analyze sales data, identify trends, provide actionable advice
- Input: subcategory, date, amount, is_forecast
- Output: Structured Danish advice (max 300 words)
- Guidelines: Concise, no technical jargon, concrete actions

---

## src/integrations Directory

### src/integrations/dandomain/modern.py
**Purpose:** DanDomain Modern GraphQL API integration

**Functions:**

1. **getDandomainToken(tenant, client_id, client_secret)**
   - OAuth client credentials flow
   - Returns access token for authenticated requests

2. **getOrders(token, tenant, page_size=100, max_pages=1000)**
   - GraphQL pagination query
   - Returns dict with DataFrames:
     - orders (order_id indexed)
     - customers (customer_id indexed)
     - order_lines (order_line_id indexed)
     - languages (language_id indexed)
   - Fetches all pages until empty

3. **getProducts(token, tenant)**
   - GraphQL query for products
   - Returns dict with products DataFrame
   - Fields: id, stock, price, cost, discount, categories, brand

4. **getProductCategories(token, tenant)**
   - GraphQL query for category tree
   - Fetches categories with labels (titles)
   - Returns dict with product_categories DataFrame
   - Includes path and title mapping

**GraphQL Query Structure:**
- Orders: id, totalItems, total, currency, customer, orderLines, language
- Products: content with id, stock, pricing, categories, brand
- Categories: content with id, path, timestamps
- Category Tree: content with id, title for each language

---

### src/integrations/dandomain/classic.py
**Purpose:** DanDomain Classic REST API integration

**Functions:**

1. **testDandomainClassicConnection(api_key, tenant)**
   - Test connectivity with recent order fetch
   - Prints connection status and sample data

2. **getOrders(api_key, tenant, max_pages=50, latest_order_date="9999-12-31 23:59:59")**
   - Fetches orders by month intervals (reverse chronological)
   - Stops at latest_order_date to avoid re-fetching
   - Returns dict with DataFrames:
     - orders (order_id indexed)
     - customers (customer_id indexed)
     - order_lines (order_line_id indexed)
     - languages (language_id indexed)
   - Handles Classic API date format: `/Date(ms+tz)/`

3. **getProducts(api_key, tenant)**
   - Uses Basic Authentication (metly:api_key)
   - Paginates through main categories
   - Fetches subcategories for each main category
   - Fetches products for each subcategory
   - Merges category names into product DataFrame
   - Returns DataFrame with: productNumber, productName, subcategory_name, maincategory_name

**Date Parsing:**
- Parses DanDomain `/Date(-123456789+0200)/` format
- Handles timezone offset
- Returns formatted datetime string

**API Endpoints:**
- Orders: `/admin/webapi/Endpoints/v1_0/OrderService`
- Products: `/admin/WebAPI/v2/sites/{site_id}/categories`

---

### src/integrations/demo/demo.py
**Purpose:** Generate realistic demo golf equipment sales data

**Functions:**

1. **makeDummyData(conn, user_id)**
   - Deletes existing demo data for user
   - Generates 1 year of golf sales data
   - Creates products (14 categories, 60+ products)
   - Generates customers (Danish names, addresses)
   - Generates orders (5-15 per day, seasonal variation)
   - Inserts all data in chunks

2. **Helper Functions:**
   - `_generate_customer_id()`, `_generate_order_id()`, etc.
   - `_generate_customer()`: Random Danish customer
   - `_get_daily_order_count()`: Seasonal order volume
   - `_select_products_for_order()`: Product selection logic

**Product Categories:**
- Drivere, Fairway Træer, Hybrider, Jernsæt
- Wedges, Puttere, Golfbolde, Golftasker
- Golfhandsker, Golfsko, Afstandsmålere, GPS Ure
- Træningshjælpemidler, Golftøj, Golftilbehør

**Seasonal Patterns:**
- Monthly trends (e.g., May/June peak, January slow)
- Weekend boost (1.3x)
- Category popularity weights

**Customer Data:**
- Danish first/last names
- Real Danish cities/zip codes
- Realistic street names

---

## Database Schema Reference

### Foreign Key Relationships
- All data tables → users.id (ON DELETE SET NULL)
- orders.customer_id → customers.id
- orders.language_id → languages.id
- order_lines.order_id → orders.id
- order_lines.product_id → products.id (Classic)
- products.subcategory_id → product_categories.id (Classic)

### Indexes
- All tables: idx_{table}_user_id (user_id)
- orders: idx_orders_createdAt (createdAt)
- order_lines: idx_order_lines_order_id, idx_order_lines_product_id
- Composite: idx_ol_user_prod_order (user_id, product_id, order_id)
- forecasts: UNIQUE (date, subcategory_name, user_id)

---

## Key Design Patterns

### Multi-Tenant Isolation
- Every data table includes `user_id` column
- FK to users.id ensures referential integrity
- Queries always filter by `user_id`
- Users can only access their own data

### Read-Only Integration
- All integrations only fetch data (GET/POST for GraphQL)
- No write/update/delete operations on external APIs
- Data written only to local database

### Error Handling
- Retry logic with exponential backoff
- Graceful degradation (fallback predictions)
- Transaction management with rollback on failure
- Comprehensive logging

### Performance
- Chunked inserts (1000 rows)
- Connection pooling (SQLAlchemy)
- Thread-limited numerical libraries
- Optimized indexes for common queries

---

## Environment Variables Required

For Local Development:
```
DB_USR=              # App database user
DB_PWD=              # App database password
DB_USR_ADMIN=         # Admin database user (for main.py)
DB_PWD_ADMIN=         # Admin database password (for main.py)
JWT_SECRET=           # JWT signing secret
JWT_ALGORITHM=        # JWT algorithm (HS256)
GEMINI_API_KEY=      # Google Gemini API key
```

---

## Running the Application

### Batch Operations (main.py)
```bash
python main.py
```
Steps: Create tables → Fetch data → Predict sales → Get AI advice

### Development Server (FastAPI)
```bash
uvicorn src.endpoints.getData:app --reload --host 0.0.0.0 --port 8000
```
Access: http://localhost:8000/docs

### Passenger Hosting
Deploy passenger_wsgi.py - automatically handles ASGI→WSGI conversion

---

## Common Workflows

### Adding a New User
1. Run createUser() in createDB.py with platform, email, api_key, tenant
2. System generates random password (hashed with bcrypt)
3. Save the displayed password (cannot be recovered)
4. User logs in via /auth/login endpoint

### Generating Daily Forecasts
1. Run main.py or call predictSales() directly
2. System fetches latest data from integrations
3. Trains LightGBM models per subcategory
4. Stores forecasts in forecasts table
5. Forecasts available via /forecasts endpoint

### Getting AI Business Advice
1. Ensure forecasts exist for user
2. Run get_business_advice() (included in main.py)
3. System sends forecast data to Gemini AI
4. Returns Danish business advice
5. Advice available via /forecast_business_advice endpoint

---

## Security Notes

### Password Management
- All passwords stored as bcrypt hashes
- Minimum 12 characters (truncated for bcrypt limit)
- Migration script available for legacy plaintext passwords
- One-way hash - passwords cannot be recovered

### API Security
- JWT tokens expire after 24 hours
- Token subject (sub) must be valid UUID
- Users can only query their own data
- Generic error messages prevent enumeration

### Database Security
- Parameterized queries prevent SQL injection
- Separate app/admin database users
- Least privilege principle

---

## Known Limitations

1. **Incomplete Modules:**
   - src/scripts/db/connections.py (stub)
   - src/scripts/analysis/customers.py (incomplete)
   - src/scripts/analysis/products.py (incomplete)

2. **Platform Support:**
   - Dandomain Modern: Full support
   - Dandomain Classic: Full support
   - Demo: Full support
   - Shopify: Structure ready, not implemented

3. **Forecasting:**
   - Requires minimum 120 days of data
   - Falls back to linear trend for sparse data
   - Low-volume categories may have limited accuracy

---

## File Dependencies Graph

```
main.py
  ├─> createDB.py
  │    ├─> createTables.sql
  │    └─> populateDB.py
  │         ├─> modern.py
  │         ├─> classic.py
  │         └─> demo.py
  ├─> predictSales.py
  └─> consultAi.py

getData.py (FastAPI)
  ├─> populateDB.py (connectDB)
  ├─> .env (credentials)
  └─> python-jose (JWT)
```

---

## AI-Specific Instructions

When working with this codebase:

1. **Always maintain multi-tenant isolation** - never query without user_id filter
2. **Never write to external APIs** - integrations are read-only by design
3. **Use parameterized queries** - SQL injection prevention is critical
4. **Follow logging patterns** - use logger.info/warning/error with structured data
5. **Handle sparse data gracefully** - many categories have low sales volumes
6. **Respect bcrypt password limits** - truncate to 72 bytes/12 chars
7. **Use chunked inserts** - 1000 rows per batch for performance
8. **Test with demo data** - use demo.py for realistic test data

---

**Document Version:** 2025-01-22
**Repository:** /home/rasmus/Work/metly_backend
