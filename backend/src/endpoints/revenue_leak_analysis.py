"""
Revenue Leak Analysis API Endpoint

Provides analysis of revenue leakage from:
- Failed payments
- Cancelled orders
- Refunds

Returns metrics: failed payment %, cancellation rate, refund rate,
grouped by payment method, product category, and time period.
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
        from jose import jwt, JWTError

        return jwt, JWTError
    except Exception as exc:
        raise RuntimeError(
            "Missing dependency 'python-jose'. Install with: pip install 'python-jose[cryptography]'"
        ) from exc


conn = None
JWT_SECRET = None
JWT_ALGORITHM = None


def _init_revenue_leak_globals(db_conn, jwt_secret, jwt_algo):
    """Initialize globals from parent app."""
    global conn, JWT_SECRET, JWT_ALGORITHM
    conn = db_conn
    JWT_SECRET = jwt_secret
    JWT_ALGORITHM = jwt_algo
    logger.info("Initialized revenue leak analysis module")


def _require_auth():
    """Validate JWT token and return user_id."""
    jose, JWTError = _require_jose()

    def validate(credentials: HTTPAuthorizationCredentials = Depends(security)):
        if not credentials:
            raise HTTPException(status_code=401, detail="Missing authorization")
        token = credentials.credentials
        try:
            payload = jose.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")
            return user_id
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    return validate


class RevenueLeakResponse(BaseModel):
    order_count: int
    total_revenue: float
    failed_payment_count: int
    failed_payment_revenue: float
    failed_payment_pct: float
    cancelled_count: int
    cancelled_revenue: float
    cancelled_pct: float
    refunded_count: int
    refunded_revenue: float
    refunded_pct: float
    total_leak_count: int
    total_leak_revenue: float
    total_leak_pct: float
    leak_by_status: list
    leak_by_month: list


@router.get("/revenue_leak_analysis", response_model=RevenueLeakResponse)
def get_revenue_leak_analysis(user_id: UUID = Depends(_require_auth())):
    """
    Analyze revenue leakage for orders.

    Returns metrics on:
    - Failed payments (payment failed status)
    - Cancelled orders
    - Refunded orders

    Grouped by status and month for trend analysis.
    """
    logger.info(f"Revenue leak analysis request for user: {user_id}")

    if conn is None:
        logger.error("No database connection available")
        raise HTTPException(status_code=500, detail="Database connection unavailable")

    try:
        with conn._sqlalchemy_engine.connect() as db_conn:
            orders_query = text("""
                SELECT 
                    id,
                    total,
                    orderStatus,
                    createdAt,
                    cancelledAt,
                    fulfillment_status
                FROM metlydk_main.orders
                WHERE user_id = :user_id
            """)

            df = pd.read_sql(orders_query, db_conn, params={"user_id": str(user_id)})

            logger.info(f"Found {len(df)} orders for analysis")

            if df.empty:
                return RevenueLeakResponse(
                    order_count=0,
                    total_revenue=0.0,
                    failed_payment_count=0,
                    failed_payment_revenue=0.0,
                    failed_payment_pct=0.0,
                    cancelled_count=0,
                    cancelled_revenue=0.0,
                    cancelled_pct=0.0,
                    refunded_count=0,
                    refunded_revenue=0.0,
                    refunded_pct=0.0,
                    total_leak_count=0,
                    total_leak_revenue=0.0,
                    total_leak_pct=0.0,
                    leak_by_status=[],
                    leak_by_month=[],
                )

            total_orders = len(df)
            total_revenue = df["total"].sum() if "total" in df.columns else 0.0

            df["orderStatus"] = df["orderStatus"].fillna("unknown")

            failed_mask = (
                df["orderStatus"]
                .str.lower()
                .isin(["payment_failed", "failed", "declined"])
            )
            failed_payment_count = failed_mask.sum()
            failed_payment_revenue = (
                df.loc[failed_mask, "total"].sum() if "total" in df.columns else 0.0
            )

            cancelled_mask = (
                df["orderStatus"].str.lower().isin(["cancelled", "canceled"])
            )
            cancelled_count = cancelled_mask.sum()
            cancelled_revenue = (
                df.loc[cancelled_mask, "total"].sum() if "total" in df.columns else 0.0
            )

            refunded_mask = df["orderStatus"].str.lower().isin(["refunded", "refund"])
            refunded_count = refunded_mask.sum()
            refunded_revenue = (
                df.loc[refunded_mask, "total"].sum() if "total" in df.columns else 0.0
            )

            total_leak_count = failed_payment_count + cancelled_count + refunded_count
            total_leak_revenue = (
                failed_payment_revenue + cancelled_revenue + refunded_revenue
            )

            failed_payment_pct = (
                (failed_payment_count / total_orders * 100) if total_orders > 0 else 0.0
            )
            cancelled_pct = (
                (cancelled_count / total_orders * 100) if total_orders > 0 else 0.0
            )
            refunded_pct = (
                (refunded_count / total_orders * 100) if total_orders > 0 else 0.0
            )
            total_leak_pct = (
                (total_leak_count / total_orders * 100) if total_orders > 0 else 0.0
            )

            status_groups = (
                df.groupby("orderStatus")
                .agg(count=("id", "count"), revenue=("total", "sum"))
                .reset_index()
            )

            leak_by_status = [
                {
                    "status": row["orderStatus"],
                    "count": int(row["count"]),
                    "revenue": float(row["revenue"]),
                }
                for _, row in status_groups.iterrows()
                if row["orderStatus"].lower()
                in [
                    "payment_failed",
                    "failed",
                    "declined",
                    "cancelled",
                    "canceled",
                    "refunded",
                ]
            ]

            if "createdAt" in df.columns:
                df["month"] = pd.to_datetime(df["createdAt"]).dt.to_period("M")
                monthly_groups = (
                    df.groupby("month")
                    .agg(
                        total_orders=("id", "count"),
                        total_revenue=("total", "sum"),
                        failed=(
                            "orderStatus",
                            lambda x: (
                                x.str.lower().isin(
                                    ["payment_failed", "failed", "declined"]
                                )
                            ).sum(),
                        ),
                        cancelled=(
                            "orderStatus",
                            lambda x: (
                                x.str.lower().isin(["cancelled", "canceled"])
                            ).sum(),
                        ),
                        refunded=(
                            "orderStatus",
                            lambda x: (x.str.lower().isin(["refunded"])).sum(),
                        ),
                    )
                    .reset_index()
                )

                leak_by_month = [
                    {
                        "month": str(row["month"]),
                        "total_orders": int(row["total_orders"]),
                        "total_revenue": float(row["total_revenue"]),
                        "failed": int(row["failed"]),
                        "cancelled": int(row["cancelled"]),
                        "refunded": int(row["refunded"]),
                    }
                    for _, row in monthly_groups.iterrows()
                ]
            else:
                leak_by_month = []

            logger.info(
                f"Revenue leak analysis complete: {total_leak_count} leaks (${total_leak_revenue:.2f})"
            )

            return RevenueLeakResponse(
                order_count=total_orders,
                total_revenue=float(total_revenue),
                failed_payment_count=int(failed_payment_count),
                failed_payment_revenue=float(failed_payment_revenue),
                failed_payment_pct=float(failed_payment_pct),
                cancelled_count=int(cancelled_count),
                cancelled_revenue=float(cancelled_revenue),
                cancelled_pct=float(cancelled_pct),
                refunded_count=int(refunded_count),
                refunded_revenue=float(refunded_revenue),
                refunded_pct=float(refunded_pct),
                total_leak_count=int(total_leak_count),
                total_leak_revenue=float(total_leak_revenue),
                total_leak_pct=float(total_leak_pct),
                leak_by_status=leak_by_status,
                leak_by_month=leak_by_month,
            )

    except Exception as e:
        logger.error(f"Failed to calculate revenue leak metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate analysis")
