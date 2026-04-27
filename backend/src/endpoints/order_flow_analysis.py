"""
Order Flow Analysis API Endpoint

Provides analysis of order lifecycle stages:
- Created → Processed (payment)
- Processed → Fulfilled (shipped)
- Fulfilled → Closed

Returns duration metrics (median, P95, P99), bottleneck percentages,
fulfillment rates, and top carriers.
"""

from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import text
from uuid import UUID

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

security = HTTPBearer()


def _require_jose():
    try:
        from jose import jwt, JWTError  # type: ignore

        return jwt, JWTError
    except Exception as exc:
        raise RuntimeError(
            "Missing dependency 'python-jose'. Install with: pip install 'python-jose[cryptography]'"
        ) from exc


# Globals set by getData.py
conn = None
JWT_SECRET = None
JWT_ALGORITHM = None


def _init_order_flow_globals(db_conn, jwt_secret, jwt_algo):
    """Initialize globals from parent app."""
    global conn, JWT_SECRET, JWT_ALGORITHM
    conn = db_conn
    JWT_SECRET = jwt_secret
    JWT_ALGORITHM = jwt_algo


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    """Validate the Bearer JWT and return the subject as a UUID."""
    if not JWT_SECRET:
        raise HTTPException(status_code=500, detail="Server not configured")
    token = credentials.credentials
    jwt, JWTError = _require_jose()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token missing subject (sub)")
    try:
        return UUID(sub)
    except Exception:
        raise HTTPException(status_code=401, detail="Token subject is not a valid UUID")


class StageDuration(BaseModel):
    median_hours: float
    p95_hours: float
    p99_hours: float


class StageDurationDays(BaseModel):
    median_days: float
    p95_days: float
    p99_days: float


class CarrierCount(BaseModel):
    carrier: str
    count: int


class StageChartEntry(BaseModel):
    stage: str
    avg_hours: float


class OrderFlowAnalysisResponse(BaseModel):
    order_count: int
    stage_durations: dict
    bottlenecks: dict
    fulfillment_rate: float
    top_carriers: list[CarrierCount]
    stage_chart_data: list[StageChartEntry]


def _parse_iso_timestamp(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO timestamp string to datetime."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _get_column(df: pd.DataFrame, *names: str) -> pd.Series:
    """Get a column by trying multiple possible names (camelCase or snake_case)."""
    for name in names:
        if name in df.columns:
            return df[name]
    # Fallback: try case-insensitive match
    for name in names:
        lower_name = name.lower()
        for col in df.columns:
            if col.lower() == lower_name:
                return df[col]
    raise KeyError(f"None of the columns found: {names}. Available: {df.columns.tolist()}")


def _calculate_percentile(series: pd.Series, percentile: float) -> float:
    """Calculate percentile from a series, ignoring NaN values."""
    if series.empty or series.isna().all():
        return 0.0
    valid = series.dropna()
    if valid.empty:
        return 0.0
    return float(valid.quantile(percentile))


def _calculate_durations(orders_df: pd.DataFrame) -> dict:
    """Calculate stage durations from orders DataFrame."""
    if orders_df.empty:
        return {
            "created_to_processed": {
                "median_hours": 0.0,
                "p95_hours": 0.0,
                "p99_hours": 0.0,
            },
            "processed_to_fulfilled": {
                "median_hours": 0.0,
                "p95_hours": 0.0,
                "p99_hours": 0.0,
            },
            "fulfilled_to_closed": {
                "median_days": 0.0,
                "p95_days": 0.0,
                "p99_days": 0.0,
            },
        }

    # Parse timestamps - handle both camelCase and snake_case column names
    created_at = _get_column(orders_df, "createdAt", "created_at").apply(_parse_iso_timestamp)
    processed_at = _get_column(orders_df, "processedAt", "processed_at").apply(_parse_iso_timestamp)
    fulfilled_at = _get_column(orders_df, "fulfilledAt", "fulfilled_at").apply(_parse_iso_timestamp)
    closed_at = _get_column(orders_df, "closedAt", "closed_at").apply(_parse_iso_timestamp)

    # Calculate durations in hours
    created_to_processed = []
    processed_to_fulfilled = []
    fulfilled_to_closed = []

    for i in range(len(orders_df)):
        created = created_at.iloc[i]
        processed = processed_at.iloc[i]
        fulfilled = fulfilled_at.iloc[i]
        closed = closed_at.iloc[i]

        # Created → Processed (in hours)
        if created and processed:
            delta = (processed - created).total_seconds() / 3600
            if delta >= 0:
                created_to_processed.append(delta)

        # Processed → Fulfilled (in hours)
        if processed and fulfilled:
            delta = (fulfilled - processed).total_seconds() / 3600
            if delta >= 0:
                processed_to_fulfilled.append(delta)

        # Fulfilled → Closed (in days)
        if fulfilled and closed:
            delta = (closed - fulfilled).total_seconds() / 86400
            if delta >= 0:
                fulfilled_to_closed.append(delta)

    # Convert to series for percentile calculation
    created_to_processed_sr = pd.Series(created_to_processed)
    processed_to_fulfilled_sr = pd.Series(processed_to_fulfilled)
    fulfilled_to_closed_sr = pd.Series(fulfilled_to_closed)

    return {
        "created_to_processed": {
            "median_hours": _calculate_percentile(created_to_processed_sr, 0.5),
            "p95_hours": _calculate_percentile(created_to_processed_sr, 0.95),
            "p99_hours": _calculate_percentile(created_to_processed_sr, 0.99),
        },
        "processed_to_fulfilled": {
            "median_hours": _calculate_percentile(processed_to_fulfilled_sr, 0.5),
            "p95_hours": _calculate_percentile(processed_to_fulfilled_sr, 0.95),
            "p99_hours": _calculate_percentile(processed_to_fulfilled_sr, 0.99),
        },
        "fulfilled_to_closed": {
            "median_days": _calculate_percentile(fulfilled_to_closed_sr, 0.5),
            "p95_days": _calculate_percentile(fulfilled_to_closed_sr, 0.95),
            "p99_days": _calculate_percentile(fulfilled_to_closed_sr, 0.99),
        },
    }


def _calculate_bottlenecks(orders_df: pd.DataFrame) -> dict:
    """Calculate bottleneck percentages."""
    if orders_df.empty:
        return {
            "created_to_processed_exceeds_24h_pct": 0.0,
            "processed_to_fulfilled_exceeds_48h_pct": 0.0,
        }

    total = len(orders_df)
    if total == 0:
        return {
            "created_to_processed_exceeds_24h_pct": 0.0,
            "processed_to_fulfilled_exceeds_48h_pct": 0.0,
        }

    # Parse timestamps - handle both camelCase and snake_case column names
    created_at = _get_column(orders_df, "createdAt", "created_at").apply(_parse_iso_timestamp)
    processed_at = _get_column(orders_df, "processedAt", "processed_at").apply(_parse_iso_timestamp)
    fulfilled_at = _get_column(orders_df, "fulfilledAt", "fulfilled_at").apply(_parse_iso_timestamp)

    exceeds_24h_count = 0
    exceeds_48h_count = 0

    for i in range(len(orders_df)):
        created = created_at.iloc[i]
        processed = processed_at.iloc[i]
        fulfilled = fulfilled_at.iloc[i]

        # Check created→processed > 24h
        if created and processed:
            delta = (processed - created).total_seconds() / 3600
            if delta > 24:
                exceeds_24h_count += 1

        # Check processed→fulfilled > 48h
        if processed and fulfilled:
            delta = (fulfilled - processed).total_seconds() / 3600
            if delta > 48:
                exceeds_48h_count += 1

    return {
        "created_to_processed_exceeds_24h_pct": (exceeds_24h_count / total) * 100,
        "processed_to_fulfilled_exceeds_48h_pct": (exceeds_48h_count / total) * 100,
    }


def _calculate_fulfillment_rate(orders_df: pd.DataFrame) -> float:
    """Calculate fulfillment rate (orders with tracking / total orders)."""
    if orders_df.empty:
        return 0.0

    total = len(orders_df)
    if total == 0:
        return 0.0

    with_tracking = orders_df["tracking_number"].notna().sum()
    return (with_tracking / total) * 100


def _get_top_carriers(orders_df: pd.DataFrame, top_n: int = 5) -> list:
    """Get top carriers by count."""
    if orders_df.empty:
        return []

    carrier_counts = (
        orders_df[orders_df["carrier"].notna()]["carrier"].value_counts().head(top_n)
    )

    return [
        {"carrier": carrier, "count": int(count)}
        for carrier, count in carrier_counts.items()
    ]


def _get_stage_chart_data(durations: dict) -> list:
    """Generate stage chart data for visualization."""
    return [
        {
            "stage": "Oprettet → Behandlet",
            "avg_hours": (
                durations.get("created_to_processed", {}).get("median_hours", 0) or 0
            ),
        },
        {
            "stage": "Behandlet → Afsendt",
            "avg_hours": (
                durations.get("processed_to_fulfilled", {}).get("median_hours", 0) or 0
            ),
        },
        {
            "stage": "Afsendt → Lukket",
            "avg_hours": (
                durations.get("fulfilled_to_closed", {}).get("median_days", 0) or 0
            ),
        },
    ]


def _fetch_orders_with_fulfillment(user_id: UUID) -> pd.DataFrame:
    """Fetch orders with fulfillment data from database."""
    sql = text(
        """
        SELECT
            o.id,
            o.createdAt,
            o.processed_at,
            o.fulfilled_at,
            o.cancelled_at,
            o.closed_at,
            o.fulfillment_status,
            o.tracking_number,
            o.carrier,
            o.shipping_address
        FROM orders o
        WHERE o.user_id = :user_id
        ORDER BY o.createdAt DESC
        """
    )

    if conn is None or not hasattr(conn, "_sqlalchemy_engine"):
        raise HTTPException(status_code=500, detail="Database connection unavailable")

    try:
        df = pd.read_sql_query(
            sql, conn._sqlalchemy_engine, params={"user_id": str(user_id)}
        )
        return df
    except Exception as e:
        logger.error(f"Failed to fetch orders: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch orders")


@router.get("/order_flow_analysis", response_model=OrderFlowAnalysisResponse)
def get_order_flow_analysis(
    user_id: Optional[UUID] = Query(
        None,
        description="UUID of the user to fetch analysis for (optional; if omitted, token subject is used)",
    ),
    start_date: Optional[str] = Query(
        None,
        description="Start date filter (ISO 8601 format)",
    ),
    end_date: Optional[str] = Query(
        None,
        description="End date filter (ISO 8601 format)",
    ),
    current_user: UUID = Depends(get_current_user),
):
    """
    Get order flow analysis with stage durations and fulfillment metrics.

    Calculates durations between order lifecycle stages:
    - Created → Processed (payment captured)
    - Processed → Fulfilled (shipped)
    - Fulfilled → Closed

    Returns median, P95, P99 durations, bottleneck percentages,
    fulfillment rate, and top carriers.
    """
    user_to_query = user_id or current_user

    logger.info(f"Order flow analysis request for user: {user_to_query}")

    # Validate date parameters
    try:
        if start_date:
            datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if end_date:
            datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use ISO 8601."
        )

    # Fetch orders from database
    try:
        orders_df = _fetch_orders_with_fulfillment(user_to_query)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch orders: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch orders")

    # Apply date filters if provided
    if start_date:
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        created_col = _get_column(orders_df, "createdAt", "created_at")
        orders_df = orders_df[created_col >= start_dt]

    if end_date:
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        created_col = _get_column(orders_df, "createdAt", "created_at")
        orders_df = orders_df[created_col <= end_dt]

    order_count = len(orders_df)
    logger.info(f"Found {order_count} orders for analysis")

    # Calculate metrics
    logger.info(f"DataFrame columns: {orders_df.columns.tolist()}")
    logger.info(f"DataFrame dtypes:\n{orders_df.dtypes}")
    try:
        stage_durations = _calculate_durations(orders_df)
        bottlenecks = _calculate_bottlenecks(orders_df)
        fulfillment_rate = _calculate_fulfillment_rate(orders_df)
        top_carriers = _get_top_carriers(orders_df)
        stage_chart_data = _get_stage_chart_data(stage_durations)
    except Exception as e:
        logger.error(f"Failed to calculate metrics: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to calculate analysis")

    return OrderFlowAnalysisResponse(
        order_count=order_count,
        stage_durations=stage_durations,
        bottlenecks=bottlenecks,
        fulfillment_rate=fulfillment_rate,
        top_carriers=top_carriers,
        stage_chart_data=stage_chart_data,
    )
