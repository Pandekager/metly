# Customer Analytics Feature - Design Document

## Overview
Add customer analytics to the Metly dashboard, showing:
- Bar chart: Number of orders per city and revenue per city
- Interactive map: Customer distribution across Danish cities with markers sized by order volume and colored by revenue

## Data Model (Existing)
- `customers` table: `user_id`, `billing_city`, `id`, etc.
- `orders` table: `customer_id`, `total`, etc.
- Multi-tenant isolation via `user_id` filtering

## Backend Implementation

### 1. Demo Data Generation
**File**: `src/scripts/db/populateDemoCustomers.py` (new)

Create a script to generate demo customer data:
- For each existing user, create 50 customers distributed across 10 Danish cities
- Cities: Copenhagen, Aarhus, Odense, Aalborg, Esbjerg, Randers, Kolding, Horsens, Viborg, Silkeborg
- Assign realistic names and addresses
- Link these customers to existing orders (some orders already exist)

### 2. New API Endpoint
**File**: `src/endpoints/customerAnalytics.py` (new)

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

router = APIRouter()

class CityAnalytics(BaseModel):
    city: str
    order_count: int
    revenue: float
    latitude: float
    longitude: float

class AnalyticsResponse(BaseModel):
    data: List[CityAnalytics]

@router.get("/customer_analytics", response_model=AnalyticsResponse)
def get_customer_analytics(current_user: UUID = Depends(get_current_user)):
    """Returns aggregated customer analytics by city for the authenticated user."""
    # Query joining customers and orders, grouped by city
    # Include geocoded coordinates
    # All queries filter by user_id
```

**Geocoding**: Simple dictionary mapping city names to coordinates:
```python
CITY_COORDINATES = {
    "Copenhagen": (55.6761, 12.5683),
    "Aarhus": (56.1629, 10.2039),
    # ... etc
}
```

### 3. Register Route
Update `src/endpoints/getData.py` to include the new router:
```python
from .customerAnalytics import router as customer_analytics_router
app.include_router(customer_analytics_router)
```

## Frontend Implementation

### 1. Analytics Page/Component
**File**: `pages/analytics.vue` (new) or add to `pages/home.vue`

Use `<script setup lang="ts">` with Composition API.

### 2. Bar Chart Component
**File**: `components/charts/CityBarChart.vue` (new)

Use Chart.js (already in dependencies):
- Two datasets: Orders count (bar) and Revenue (line or secondary bar)
- Responsive, tooltips, legend
- Fetch data from `/api/customer_analytics`

### 3. Map Component
**File**: `components/maps/CustomerMap.vue` (new)

Use Leaflet (open source, free):
```bash
pnpm add leaflet vue-leaflet
```
- OpenStreetMap tiles (free)
- Circle markers with:
  - radius proportional to order count
  - color gradient based on revenue
- Popup on hover showing city name, orders, revenue

### 4. Data Fetching
- Use `$fetch` from Nuxt to get `/api/customer_analytics`
- Type-safe interfaces for response
- Error handling and loading states

## Security & Multi-Tenant Isolation
- All backend queries filter by `user_id` from JWT token
- `get_current_user()` dependency ensures authentication
- User can only see their own customers and order data
- No data leakage between tenants

## Demo Data Considerations
- The existing database may have sparse customer city data
- The new demo generation script will ensure 50 customers per user across 10 cities
- For production, this script should be run once or as needed

## Performance
- Queries should use indexes on `user_id` and `city`
- Limit city results to top 10-15 cities for the map/bar chart
- Cache geocoding results

## Testing
- Unit tests for backend aggregation queries
- Test multi-tenant isolation
- Frontend component tests with mock data

## Acceptance Criteria
- [ ] Backend endpoint returns correct aggregated data per user
- [ ] Demo data generator creates realistic customer distribution
- [ ] Bar chart displays orders and revenue per city
- [ ] Map shows markers for each city with correct sizing/coloring
- [ ] All data properly isolated by user_id
- [ ] Works with existing JWT authentication flow