# Coding Conventions

**Analysis Date:** 2026-04-13

## Naming Patterns

**Files:**
- Vue components: PascalCase (e.g., `ForecastChart.vue`, `CustomerMap.vue`)
- Server routes: kebab-case with HTTP method (e.g., `login.post.ts`, `forecasts.get.ts`)
- Python modules: snake_case (e.g., `predictSales.py`, `populateDB.py`)
- TypeScript types/interfaces: PascalCase (e.g., `Forecast.ts`, `Login.ts`)

**Functions/Methods:**
- TypeScript: camelCase (e.g., `fetchForecasts`, `setUser`)
- Python: snake_case (e.g., `connectDB`, `get_current_user`)

**Variables:**
- camelCase in both TypeScript and Python
- Private methods prefixed with underscore in Python (`_normalize_platform_name`)

**Types/Classes:**
- PascalCase (e.g., `Forecast`, `CityAnalytics`, `LoginRequest`)

## Code Style

**Frontend (Vue/TypeScript):**
- Use `<script setup lang="ts">` syntax
- Use TypeScript for all components
- Prefer `ref()` for reactive state, `computed()` for derived values

**Python:**
- Type hints for function parameters and return values
- Use `Optional[T]` from typing for nullable types

**Formatting:**
- No explicit formatter configured (per AGENTS.md)
- Tailwind CSS for styling (classes in kebab-case)

**Linting:**
- No explicit linter configured (per AGENTS.md)
- TypeScript compiler provides type checking

## Import Organization

**Frontend (TypeScript/Vue):**
1. Vue imports (`ref`, `computed`, `onMounted`)
2. Nuxt/framework imports (`useRoute`, `useRouter`)
3. Third-party libraries (`chart.js`, `leaflet`)
4. Local imports (components, stores, types, utils)

```typescript
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'nuxt'
import Chart from 'chart.js'
import { useAuthStore } from '~/stores/auth'
import type { Forecast } from '~/types/forecast'
```

**Python:**
1. Standard library (`os`, `logging`, `typing`)
2. Third-party (`fastapi`, `pandas`, `sqlalchemy`)
3. Local imports (relative imports within project)

```python
import os
import logging
from typing import List, Optional
import pandas as pd
from fastapi import FastAPI
from ..scripts.db.populateDB import connectDB
```

## Error Handling

**Frontend:**
- Use try-catch for async operations
- Use `createError` for user-facing errors
- Log errors with `console.error`

```typescript
try {
  forecasts.value = await $fetch<Forecast[]>("/api/forecasts");
} catch (error) {
  console.error("Failed to fetch forecasts:", error);
}
```

**Python:**
- Use FastAPI `HTTPException` for API errors
- Structured logging with context
- Generic error messages to prevent enumeration

```python
try:
    response = httpx.post(url, headers=headers, json=payload)
    response.raise_for_status()
except httpx.HTTPStatusError as e:
    logger.error(f"HTTP error: {e.response.status_code}")
    raise HTTPException(status_code=e.response.status_code, detail="API error")
```

## Logging

**Frontend:** `console.log`, `console.error`
**Python:** `logging` module with `logger = logging.getLogger(__name__)`

## Comments

**When to Comment:**
- Complex business logic
- Non-obvious workarounds
- API integration details
- JSDoc/TSDoc for public functions

**JSDoc/TSDoc:**
- Use for exported functions and types
- Include parameter types and return types

```typescript
/**
 * Fetch forecasts for the authenticated user.
 * @returns Array of Forecast objects
 */
```

## Function Design

**Size:** Keep functions focused and small
**Parameters:** Use interfaces for complex objects
**Return Values:** Explicit return types preferred

## Module Design

**Exports:**
- Vue: Default exports for pages/components
- Python: Explicit function/class exports

**Barrel Files:**
- Not heavily used; components imported directly

---

*Convention analysis: 2026-04-13*