# Testing Patterns

**Analysis Date:** 2026-04-13

## Test Framework

**Not configured**

Per the AGENTS.md files in both frontend and backend:
- Frontend: "This project currently has no formal test suite"
- Backend: "No test framework currently configured"

**Recommendations when tests are added:**

**Frontend:**
- Framework: Vitest (unit tests), Playwright (E2E)
- Test files: Place alongside source files with `.test.ts` or `.spec.ts` suffix

**Backend:**
- Framework: pytest
- Run with: `pytest tests/`

## Test File Organization

**Location (when added):**
- Frontend: Alongside source files (e.g., `components/charts/ForecastChart.test.ts`)
- Backend: `tests/` directory

**Naming (when added):**
- Frontend: `.test.ts`, `.spec.ts`, `.test.vue`, `.spec.vue`
- Backend: `test_*.py` or `*_test.py`

## Test Structure (Recommended)

**Frontend (Vitest):**
```typescript
import { describe, it, expect } from 'vitest'

describe('ForecastChart', () => {
  it('renders correctly', () => {
    // Test implementation
  })
})
```

**Backend (pytest):**
```python
import pytest
from fastapi.testclient import TestClient

def test_login(client):
    response = client.post("/auth/login", json={"email": "test@test.com", "password": "password"})
    assert response.status_code == 200
```

## Mocking (Recommended)

**Frontend:**
- Use Vitest's `vi.mock()` for module mocking
- Mock `$fetch` or API calls

**Python:**
- Use `unittest.mock` or `pytest-mock`
- Mock external API calls and database connections

## Fixtures and Factories (Recommended)

**Frontend:**
- Create test utilities in `tests/utils/` or alongside test files

**Python:**
- Use pytest fixtures in `conftest.py`

## Coverage

**Current:** None enforced
**Recommendations:** Target 80%+ for business logic

---

*Testing analysis: 2026-04-13*