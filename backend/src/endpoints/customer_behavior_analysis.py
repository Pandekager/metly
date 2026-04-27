"""
Customer Behavior Analysis API Endpoint

Analyzes customer retention and lifetime value:
- Customer retention rates over time
- Cohort analysis (new vs returning customers)
- Customer lifetime value metrics
- Purchase frequency patterns

Returns metrics: retention rate, LTV, frequency distribution, cohort data.
"""

from datetime import datetime
from typing import List, Dict

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
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


def _init_customer_behavior_globals(db_conn, jwt_secret, jwt_algo):
    """Initialize globals from parent app."""
    global conn, JWT_SECRET, JWT_ALGORITHM
    conn = db_conn
    JWT_SECRET = jwt_secret
    JWT_ALGORITHM = jwt_algo
    logger.info("Initialized customer behavior analysis module")


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


class PurchaseFrequency(BaseModel):
    one_time: int
    one_time_pct: float
    regular: int
    regular_pct: float
    frequent: int
    frequent_pct: float


class MonthlyCohort(BaseModel):
    month: str
    new_customers: int
    returning_customers: int
    retention_rate: float
    total_revenue: float


class CustomerBehaviorResponse(BaseModel):
    total_customers: int
    returning_customers: int
    retention_rate: float
    avg_customer_lifetime_value: float
    total_revenue: float
    purchase_frequency: PurchaseFrequency
    monthly_cohorts: List[MonthlyCohort]


@router.get("/customer_behavior_analysis", response_model=CustomerBehaviorResponse)
def get_customer_behavior_analysis(user_id: UUID = Depends(_require_auth())):
    """
    Analyze customer behavior and retention patterns.

    Returns metrics on:
    - Total unique customers
    - Returning customers count
    - Retention rate (%)
    - Average customer lifetime value
    - Total revenue
    - Purchase frequency distribution
    - Monthly cohort trends
    """
    logger.info(f"Customer behavior analysis request for user: {user_id}")

    if conn is None:
        logger.error("No database connection available")
        raise HTTPException(status_code=500, detail="Database connection unavailable")

    try:
        with conn._sqlalchemy_engine.connect() as db_conn:
            orders_query = text("""
                SELECT 
                    id,
                    customer_id,
                    total,
                    createdAt,
                    orderStatus
                FROM metlydk_main.orders
                WHERE user_id = :user_id
                  AND orderStatus = 'completed'
            """)

            df = pd.read_sql(orders_query, db_conn, params={"user_id": str(user_id)})

            logger.info(f"Found {len(df)} orders for customer behavior analysis")

            if df.empty:
                return CustomerBehaviorResponse(
                    total_customers=0,
                    returning_customers=0,
                    retention_rate=0.0,
                    avg_customer_lifetime_value=0.0,
                    total_revenue=0.0,
                    purchase_frequency=PurchaseFrequency(
                        one_time=0,
                        one_time_pct=0.0,
                        regular=0,
                        regular_pct=0.0,
                        frequent=0,
                        frequent_pct=0.0,
                    ),
                    monthly_cohorts=[],
                )

            # Filter out null customer IDs
            df = df[df["customer_id"].notna() & (df["customer_id"] != "")]
            
            total_customers = df["customer_id"].nunique()
            total_revenue = df["total"].sum()

            # Calculate orders per customer
            customer_orders = df.groupby("customer_id").size().reset_index(name="order_count")
            
            one_time = int((customer_orders["order_count"] == 1).sum())
            regular = int((customer_orders["order_count"] >= 2) & (customer_orders["order_count"] <= 3)).sum()
            frequent = int((customer_orders["order_count"] >= 4).sum())
            
            returning_customers = regular + frequent
            retention_rate = (returning_customers / total_customers * 100) if total_customers > 0 else 0
            
            avg_ltv = (total_revenue / total_customers) if total_customers > 0 else 0

            purchase_frequency = PurchaseFrequency(
                one_time=one_time,
                one_time_pct=round(one_time / total_customers * 100, 1) if total_customers > 0 else 0,
                regular=regular,
                regular_pct=round(regular / total_customers * 100, 1) if total_customers > 0 else 0,
                frequent=frequent,
                frequent_pct=round(frequent / total_customers * 100, 1) if total_customers > 0 else 0,
            )

            # Monthly cohort analysis
            df["month"] = pd.to_datetime(df["createdAt"]).dt.to_period("M")
            
            monthly_cohorts = []
            for month in sorted(df["month"].unique()):
                month_df = df[df["month"] == month]
                month_customers = month_df["customer_id"].nunique()
                
                # Find returning customers (those who ordered in this month and also in subsequent months)
                month_customer_set = set(month_df["customer_id"].unique())
                
                # Get subsequent months
                subsequent_df = df[df["month"] > month]
                returning = 0
                monthly_revenue = 0
                
                if not subsequent_df.empty:
                    subsequent_customers = set(subsequent_df["customer_id"].unique())
                    returning = len(month_customer_set & subsequent_customers)
                    returning_customers_in_future = df[
                        (df["month"] > month) & (df["customer_id"].isin(month_customer_set))
                    ]
                    monthly_revenue = returning_customers_in_future["total"].sum()
                
                retention_rate_cohort = (returning / month_customers * 100) if month_customers > 0 else 0
                
                monthly_cohorts.append(
                    MonthlyCohort(
                        month=str(month),
                        new_customers=int(month_customers),
                        returning_customers=int(returning),
                        retention_rate=round(retention_rate_cohort, 1),
                        total_revenue=round(float(monthly_revenue), 2),
                    )
                )

            logger.info(
                f"Customer behavior analysis complete: {total_customers} customers, "
                f"{retention_rate:.1f}% retention rate, avg LTV {avg_ltv:.2f}"
            )

            return CustomerBehaviorResponse(
                total_customers=int(total_customers),
                returning_customers=int(returning_customers),
                retention_rate=round(retention_rate, 1),
                avg_customer_lifetime_value=round(avg_ltv, 2),
                total_revenue=round(float(total_revenue), 2),
                purchase_frequency=purchase_frequency,
                monthly_cohorts=monthly_cohorts,
            )

    except Exception as e:
        logger.error(f"Failed to calculate customer behavior metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate analysis")