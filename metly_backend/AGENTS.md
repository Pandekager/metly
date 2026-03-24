# AGENTS.md - Metly Backend Development Guide

This file contains guidelines and commands for agentic coding agents working in the Metly Backend repository.

## Build/Lint/Test Commands

### Development Server
```bash
# Start development server with auto-reload
uvicorn src.endpoints.getData:app --reload --host 0.0.0.0 --port 8000

# Alternative using helper script
./run_main.sh
```

### Database Operations
```bash
# Main orchestration script (creates tables, fetches data, runs analysis)
python main.py

# Test database connectivity
src/scripts/db/createDB.py authenticateDB $DB_USR $DB_PWD

# Create database tables
src/scripts/db/createDB.py createTables $DB_USR $DB_PWD
```

### Testing (No test framework currently configured)
```bash
# No test framework configured yet
# To run tests when implemented:
pytest tests/                    # Run all tests
pytest tests/test_module.py     # Run single test file
pytest tests/test_module.py::test_function  # Run single test
```

### Code Quality
```bash
# Check Python syntax
python -m py_compile src/**/*.py

# Check for common issues
flake8 src/ tests/              # If flake8 installed
```

## Code Style Guidelines

### Import Organization
```python
# Standard library imports first
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict

# Third-party imports second
import httpx
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException

# Local imports last (with relative imports when possible)
from ..scripts.db.populateDB import connectDB
from .endpoints.getData import app
```

### Type Hints
- Use type hints for all function parameters and return values
- Import from `typing` module: `List`, `Dict`, `Optional`, `Union`
- Use `Optional[T]` for nullable types
- Use `Dict[str, Any]` for dynamic dictionaries

### Naming Conventions
- **Variables/Functions**: `snake_case` (e.g., `get_orders`, `user_id`)
- **Classes**: `PascalCase` (e.g., `OrderService`, `ProductCategory`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_LIMIT`)
- **Private methods**: Prefix with underscore (e.g., `_parse_date`)

### Error Handling
```python
# Use specific exceptions
try:
    response = httpx.post(url, headers=headers, json=payload)
    response.raise_for_status()
except httpx.HTTPStatusError as e:
    logger.error(f"HTTP error: {e.response.status_code}")
    raise HTTPException(status_code=e.response.status_code, detail="API error")
except httpx.RequestError as e:
    logger.error(f"Request error: {str(e)}")
    raise HTTPException(status_code=500, detail="Connection failed")
```

### Logging Patterns
```python
import logging
logger = logging.getLogger(__name__)

# Use structured logging
logger.info("Fetched orders", page=page, count=len(orders_list))
logger.warning("API rate limit reached", remaining=rate_limit)
logger.error("Database connection failed", error=str(e))
```

### Database Patterns
```python
# Use parameterized queries to prevent SQL injection
query = text("SELECT * FROM users WHERE id = :user_id")
result = conn.execute(query, user_id=user_id)

# Always filter by user_id for multi-tenant isolation
query = text("SELECT * FROM orders WHERE user_id = :user_id")
```

### API Response Patterns
```python
# FastAPI endpoint structure
@app.get("/orders")
def get_orders(user_id: UUID = Depends(get_current_user)):
    """Get orders for authenticated user."""
    orders = fetch_orders_for_user(user_id)
    return {"data": orders, "count": len(orders)}

# Error responses
raise HTTPException(status_code=404, detail="Order not found")
```

## Multi-Tenant Architecture

### Data Isolation
- Every data table must include `user_id` column
- Always filter queries by `user_id`
- Use `get_current_user()` dependency for authentication
- Never expose data from other tenants

### User Authentication
```python
# JWT token validation
async def get_current_user(token: str = Depends(security)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception
```

## Integration Patterns

### Dandomain Integration
- **Modern API**: GraphQL-based with OAuth2 authentication
- **Classic API**: REST-based with Basic authentication
- **Read-only**: Never write to external APIs
- **Error handling**: Implement retry logic with exponential backoff

### Data Processing
```python
# Chunked database operations for performance
chunk_size = 1000
for i in range(0, len(data), chunk_size):
    chunk = data[i:i + chunk_size]
    conn.execute(insert_statement, chunk)
    conn.commit()
```

## Security Requirements

### Password Handling
- Use bcrypt for password hashing
- Minimum 12 characters (truncated for bcrypt limit)
- Never log plaintext passwords
- Use `passlib.context.CryptContext`

### SQL Injection Prevention
- Always use parameterized queries
- Never use string interpolation for SQL
- Use SQLAlchemy `text()` with named parameters

### Authentication
- JWT tokens expire after 24 hours
- Use UUID in `sub` claim for user identification
- Generic error messages to prevent enumeration

## Performance Considerations

### Thread Control
```python
# Limit numerical library threads to prevent resource exhaustion
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
```

### Connection Management
- Use connection pooling for database operations
- Implement retry logic with exponential backoff
- Close connections properly after use

## File Organization

### Directory Structure
```
src/
├── endpoints/           # FastAPI API endpoints
├── scripts/            # Database operations and utilities
│   ├── db/          # Database connection and management
│   └── analysis/     # Data analysis and ML scripts
├── integrations/       # E-commerce platform integrations
└── db/                # Database schema and migrations
```

### Module Imports
- Use relative imports for internal modules
- Import order: standard library → third-party → local
- Avoid circular dependencies

## Environment Configuration

### Required Variables
```bash
# See .env file for actual values (do not commit)
DB_USR=your_db_username
DB_PWD=your_db_password
DB_USR_ADMIN=your_admin_username
DB_PWD_ADMIN=your_admin_password
JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256
GEMINI_API_KEY=your_gemini_api_key
```

### Loading Environment
```python
from dotenv import load_dotenv
load_dotenv("./.env")
```

## Critical Design Principles

### READ-ONLY System
- **Never write to external APIs** - integrations are read-only
- **Never update/delete external data** - only fetch for analysis
- **Data written only to local database** - no external writes

### Multi-Tenant Isolation
- **Every table has user_id** - for tenant isolation
- **Always filter by user_id** - never expose other tenants' data
- **Database-level constraints** - enforce referential integrity

### Error Resilience
- **Retry logic with exponential backoff** - for API calls
- **Graceful degradation** - fallback predictions for sparse data
- **Comprehensive logging** - structured logging with context

## Development Workflow

### Adding New Features
1. Create new function in appropriate module
2. Add proper type hints and error handling
3. Implement multi-tenant isolation
4. Add logging and documentation
5. Test with demo data

### Modifying Existing Code
1. Check existing patterns and conventions
2. Update related documentation
3. Test backward compatibility
4. Verify multi-tenant isolation
5. Run syntax and style checks

---

**Repository**: `/home/rasmus/Work/metly_backend`
**Python Version**: >=3.11
**Package Manager**: Poetry
**Framework**: FastAPI with SQLAlchemy 2.0