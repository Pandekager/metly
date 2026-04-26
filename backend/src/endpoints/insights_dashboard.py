"""
Insights Dashboard API Endpoint

Aggregates data from all analysis endpoints to provide:
- Top revenue leak sources
- Top operational bottlenecks
- Top refunded products
- Key retention metrics
- Actionable recommendations with priority scores

This is the unified "single pane of glass" view for business insights.
"""

from typing import List, Optional
from datetime import datetime

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


def _init_insights_dashboard_globals(db_conn, jwt_secret, jwt_algo):
    """Initialize globals from parent app."""
    global conn, JWT_SECRET, JWT_ALGORITHM
    conn = db_conn
    JWT_SECRET = jwt_secret
    JWT_ALGORITHM = jwt_algo
    logger.info("Initialized insights dashboard module")


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


# Response Models

class RevenueLeakSource(BaseModel):
    """Top revenue leak source item."""
    type: str  # 'failed_payment', 'cancelled', 'refunded'
    count: int
    revenue: float
    percentage: float
    severity: str  # 'high', 'medium', 'low'


class BottleneckItem(BaseModel):
    """Top operational bottleneck item."""
    stage: str
    avg_duration_hours: float
    orders_count: int
    delay_rate: float
    severity: str  # 'high', 'medium', 'low'


class RefundedProductItem(BaseModel):
    """Top refunded product item."""
    product_name: str
    refund_count: int
    refund_rate: float
    revenue: float


class RetentionMetrics(BaseModel):
    """Key customer retention metrics."""
    total_customers: int
    retention_rate: float
    avg_customer_lifetime_value: float
    one_time_customer_pct: float
    frequent_customer_pct: float


class Recommendation(BaseModel):
    """Actionable business recommendation."""
    priority: int  # 1-5, 1 is highest
    category: str  # 'revenue', 'operations', 'retention', 'products'
    title: str
    description: str
    potential_impact: str  # 'high', 'medium', 'low'
    metric_focus: Optional[str] = None  # e.g., "2.5% revenue recovery"


class InsightsDashboardResponse(BaseModel):
    """Main response model for insights dashboard."""
    total_orders: int
    total_revenue: float
    total_leak_revenue: float
    leak_rate: float
    
    # Aggregated sections
    top_revenue_leaks: List[RevenueLeakSource]
    top_bottlenecks: List[BottleneckItem]
    top_refunded_products: List[RefundedProductItem]
    retention_metrics: RetentionMetrics
    
    # Recommendations
    recommendations: List[Recommendation]
    
    # Summary stats
    insights_count: int
    critical_issues: int


# Thresholds for severity classification
LEAK_SEVERITY_THRESHOLDS = {
    "high": 10.0,   # >10% of orders
    "medium": 5.0,  # >5% of orders
    "low": 0.0,    # default
}

BOTTLENECK_SEVERITY_THRESHOLDS = {
    "high": 30.0,   # >30% delay rate
    "medium": 15.0, # >15% delay rate
    "low": 0.0,     # default
}

REFUND_SEVERITY_THRESHOLDS = {
    "high": 15.0,   # >15% refund rate
    "medium": 8.0,  # >8% refund rate
    "low": 0.0,     # default
}


def _classify_severity(value: float, thresholds: dict) -> str:
    """Classify severity based on thresholds."""
    if value >= thresholds["high"]:
        return "high"
    elif value >= thresholds["medium"]:
        return "medium"
    return "low"


def _generate_recommendations(
    revenue_leaks: List[RevenueLeakSource],
    bottlenecks: List[BottleneckItem],
    refunded_products: List[RefundedProductItem],
    retention: RetentionMetrics,
) -> List[Recommendation]:
    """Generate actionable recommendations based on analysis data."""
    recommendations = []
    priority_counter = 1

    # Revenue leak recommendations
    for leak in revenue_leaks[:3]:
        if leak.severity == "high":
            if leak.type == "failed_payment":
                recommendations.append(Recommendation(
                    priority=priority_counter,
                    category="revenue",
                    title="Reduce failed payment rate",
                    description=f"Payment failures account for {leak.percentage:.1f}% of orders (€{leak.revenue:.2f} lost). Consider alternative payment providers or retry logic.",
                    potential_impact="high",
                    metric_focus=f"{leak.percentage:.1f}% recovery"
                ))
                priority_counter += 1
            elif leak.type == "cancelled":
                recommendations.append(Recommendation(
                    priority=priority_counter,
                    category="revenue",
                    title="Reduce order cancellation rate",
                    description=f"Cancellations represent {leak.percentage:.1f}% of orders (€{leak.revenue:.2f} lost). Review cart abandonment triggers and offer incentives.",
                    potential_impact="high",
                    metric_focus=f"{leak.percentage:.1f}% recovery"
                ))
                priority_counter += 1
            elif leak.type == "refunded":
                recommendations.append(Recommendation(
                    priority=priority_counter,
                    category="revenue",
                    title="Reduce refund rate",
                    description=f"Refunds account for {leak.percentage:.1f}% of orders (€{leak.revenue:.2f} lost). Improve product descriptions and expection management.",
                    potential_impact="high",
                    metric_focus=f"{leak.percentage:.1f}% recovery"
                ))
                priority_counter += 1

    # Bottleneck recommendations
    for bottleneck in bottlenecks[:2]:
        if bottleneck.severity == "high":
            recommendations.append(Recommendation(
                priority=priority_counter,
                category="operations",
                title=f"Optimize {bottleneck.stage} stage",
                description=f"Current avg: {bottleneck.avg_duration_hours:.1f}h with {bottleneck.delay_rate:.1f}% delays. Investigate process improvements.",
                potential_impact="medium",
                metric_focus=f"{bottleneck.delay_rate:.1f}% fewer delays"
            ))
            priority_counter += 1

    # Refund product recommendations
    for product in refunded_products[:2]:
        if product.refund_rate > 10.0:
            recommendations.append(Recommendation(
                priority=priority_counter,
                category="products",
                title=f"Review '{product.product_name}' for quality issues",
                description=f"High refund rate of {product.refund_rate:.1f}% ({product.refund_count} refunds). Consider quality checks or better product photos.",
                potential_impact="medium",
                metric_focus=f"{product.refund_rate:.1f}% refund rate"
            ))
            priority_counter += 1

    # Retention recommendations
    if retention.one_time_customer_pct > 60:
        recommendations.append(Recommendation(
            priority=priority_counter,
            category="retention",
            title="Improve customer retention",
            description=f"{retention.one_time_customer_pct:.1f}% of customers only order once. Implement loyalty program or targeted re-engagement campaigns.",
            potential_impact="high",
            metric_focus=f"Target {min(retention.one_time_customer_pct - 20, 30):.1f}% reduction in one-time customers"
        ))
        priority_counter += 1

    if retention.avg_customer_lifetime_value < 200:
        recommendations.append(Recommendation(
            priority=priority_counter,
            category="retention",
            title="Increase customer lifetime value",
            description=f"Average LTV is €{retention.avg_customer_lifetime_value:.2f}. Focus on cross-selling, upselling, and repeat purchase incentives.",
            potential_impact="medium",
            metric_focus="+€50 LTV target"
        ))
        priority_counter += 1

    # If no critical issues found, add general positive feedback
    if not recommendations:
        recommendations.append(Recommendation(
            priority=1,
            category="operations",
            title="Business performing well",
            description="No critical issues detected. Continue monitoring key metrics and maintain current best practices.",
            potential_impact="low",
            metric_focus="Sustained performance"
        ))

    # Sort by priority
    recommendations.sort(key=lambda x: x.priority)

    # Renumber priorities after sorting
    for i, rec in enumerate(recommendations):
        rec.priority = i + 1

    return recommendations


@router.get("/insights_dashboard", response_model=InsightsDashboardResponse)
def get_insights_dashboard(user_id: UUID = Depends(_require_auth())):
    """
    Get unified insights dashboard aggregating all analysis data.

    Returns:
    - Top revenue leak sources with severity
    - Top operational bottlenecks with delay rates
    - Top refunded products
    - Key retention metrics
    - Prioritized actionable recommendations
    """
    logger.info(f"Insights dashboard request for user: {user_id}")

    if conn is None:
        logger.error("No database connection available")
        raise HTTPException(status_code=500, detail="Database connection unavailable")

    try:
        with conn._sqlalchemy_engine.connect() as db_conn:
            # Query orders for comprehensive analysis
            orders_query = text("""
                SELECT 
                    id,
                    total,
                    orderStatus,
                    createdAt,
                    processedAt,
                    fulfilledAt,
                    carrier,
                    fulfillment_status,
                    cancelledAt,
                    closed_at as refundedAt
                FROM metlydk_main.orders
                WHERE user_id = :user_id
            """)

            df = pd.read_sql(orders_query, db_conn, params={"user_id": str(user_id)})

            logger.info(f"Found {len(df)} orders for insights dashboard")

            if df.empty:
                return InsightsDashboardResponse(
                    total_orders=0,
                    total_revenue=0.0,
                    total_leak_revenue=0.0,
                    leak_rate=0.0,
                    top_revenue_leaks=[],
                    top_bottlenecks=[],
                    top_refunded_products=[],
                    retention_metrics=RetentionMetrics(
                        total_customers=0,
                        retention_rate=0.0,
                        avg_customer_lifetime_value=0.0,
                        one_time_customer_pct=0.0,
                        frequent_customer_pct=0.0,
                    ),
                    recommendations=[
                        Recommendation(
                            priority=1,
                            category="operations",
                            title="No data available",
                            description="Connect your store to start receiving insights and recommendations.",
                            potential_impact="low",
                        )
                    ],
                    insights_count=0,
                    critical_issues=0,
                )

            total_orders = len(df)
            total_revenue = float(df["total"].sum())
            df["orderStatus"] = df["orderStatus"].fillna("unknown")

            # === REVENUE LEAK ANALYSIS ===
            failed_mask = df["orderStatus"].str.lower().isin(
                ["payment_failed", "failed", "declined"]
            )
            failed_count = int(failed_mask.sum())
            failed_revenue = float(df.loc[failed_mask, "total"].sum())

            cancelled_mask = df["orderStatus"].str.lower().isin(["cancelled", "canceled"])
            cancelled_count = int(cancelled_mask.sum())
            cancelled_revenue = float(df.loc[cancelled_mask, "total"].sum())

            refunded_mask = df["orderStatus"].str.lower().isin(["refunded", "refund"])
            refunded_count = int(refunded_mask.sum())
            refunded_revenue = float(df.loc[refunded_mask, "total"].sum())

            total_leak_count = failed_count + cancelled_count + refunded_count
            total_leak_revenue = failed_revenue + cancelled_revenue + refunded_revenue
            leak_rate = (total_leak_count / total_orders * 100) if total_orders > 0 else 0

            top_revenue_leaks = [
                RevenueLeakSource(
                    type="failed_payment",
                    count=failed_count,
                    revenue=failed_revenue,
                    percentage=(failed_count / total_orders * 100) if total_orders > 0 else 0,
                    severity=_classify_severity(
                        (failed_count / total_orders * 100) if total_orders > 0 else 0,
                        LEAK_SEVERITY_THRESHOLDS
                    ),
                ),
                RevenueLeakSource(
                    type="cancelled",
                    count=cancelled_count,
                    revenue=cancelled_revenue,
                    percentage=(cancelled_count / total_orders * 100) if total_orders > 0 else 0,
                    severity=_classify_severity(
                        (cancelled_count / total_orders * 100) if total_orders > 0 else 0,
                        LEAK_SEVERITY_THRESHOLDS
                    ),
                ),
                RevenueLeakSource(
                    type="refunded",
                    count=refunded_count,
                    revenue=refunded_revenue,
                    percentage=(refunded_count / total_orders * 100) if total_orders > 0 else 0,
                    severity=_classify_severity(
                        (refunded_count / total_orders * 100) if total_orders > 0 else 0,
                        LEAK_SEVERITY_THRESHOLDS
                    ),
                ),
            ]

            # Sort by revenue impact
            top_revenue_leaks.sort(key=lambda x: x.revenue, reverse=True)

            # === BOTTLENECK ANALYSIS ===
            created_times = pd.to_datetime(df["createdAt"], errors="coerce")
            processed_times = pd.to_datetime(df["processedAt"], errors="coerce")
            fulfilled_times = pd.to_datetime(df["fulfilledAt"], errors="coerce")

            processing_mask = created_times.notna() & processed_times.notna()
            fulfillment_mask = processed_times.notna() & fulfilled_times.notna()

            processing_hours = (processed_times - created_times).dt.total_seconds() / 3600
            fulfillment_hours = (fulfilled_times - processed_times).dt.total_seconds() / 3600

            bottlenecks = []

            # Processing bottleneck
            if processing_mask.sum() > 0:
                avg_processing = float(processing_hours[processing_mask].mean())
                processing_delayed = int((processing_hours[processing_mask] > 24).sum())
                processing_delay_rate = (
                    processing_delayed / processing_mask.sum() * 100
                    if processing_mask.sum() > 0
                    else 0
                )
                bottlenecks.append(
                    BottleneckItem(
                        stage="Ordre modtaget → Behandlet",
                        avg_duration_hours=avg_processing,
                        orders_count=int(processing_mask.sum()),
                        delay_rate=processing_delay_rate,
                        severity=_classify_severity(
                            processing_delay_rate, BOTTLENECK_SEVERITY_THRESHOLDS
                        ),
                    )
                )

            # Fulfillment bottleneck
            if fulfillment_mask.sum() > 0:
                avg_fulfillment = float(fulfillment_hours[fulfillment_mask].mean())
                fulfillment_delayed = int((fulfillment_hours[fulfillment_mask] > 48).sum())
                fulfillment_delay_rate = (
                    fulfillment_delayed / fulfillment_mask.sum() * 100
                    if fulfillment_mask.sum() > 0
                    else 0
                )
                bottlenecks.append(
                    BottleneckItem(
                        stage="Behandlet → Afsendt",
                        avg_duration_hours=avg_fulfillment,
                        orders_count=int(fulfillment_mask.sum()),
                        delay_rate=fulfillment_delay_rate,
                        severity=_classify_severity(
                            fulfillment_delay_rate, BOTTLENECK_SEVERITY_THRESHOLDS
                        ),
                    )
                )

            # Sort bottlenecks by delay rate (severity)
            top_bottlenecks = sorted(bottlenecks, key=lambda x: x.delay_rate, reverse=True)[:5]

            # === REFUND PRODUCTS ANALYSIS ===
            order_lines_query = text("""
                SELECT 
                    ol.product_id,
                    p.product_name,
                    ol.amount,
                    (ol.amount * ol.unit_revenue) as line_total
                FROM metlydk_main.order_lines ol
                JOIN metlydk_main.products p ON ol.product_id = p.id
                JOIN metlydk_main.orders o ON ol.order_id = o.id
                WHERE o.user_id = :user_id
                AND o.orderStatus IN ('refunded', 'refund')
            """)

            refund_df = pd.read_sql(order_lines_query, db_conn, params={"user_id": str(user_id)})

            # Get all products for rate calculation
            all_products_query = text("""
                SELECT 
                    ol.product_id,
                    p.product_name,
                    COUNT(*) as order_count,
                    SUM(ol.amount * ol.unit_revenue) as total_revenue
                FROM metlydk_main.order_lines ol
                JOIN metlydk_main.products p ON ol.product_id = p.id
                JOIN metlydk_main.orders o ON ol.order_id = o.id
                WHERE o.user_id = :user_id
                GROUP BY ol.product_id, p.product_name
            """)

            all_products_df = pd.read_sql(all_products_query, db_conn, params={"user_id": str(user_id)})

            top_refunded_products = []

            if not refund_df.empty and "product_id" in refund_df.columns:
                product_refunds = (
                    refund_df.groupby(["product_id", "product_name"])
                    .agg(
                        refund_count=("product_id", "count"),
                        refund_revenue=("line_total", "sum"),
                    )
                    .reset_index()
                )

                for _, row in product_refunds.iterrows():
                    product_id = row["product_id"]
                    refund_count = int(row["refund_count"])

                    # Find total orders for this product
                    product_total = all_products_df[
                        all_products_df["product_id"] == product_id
                    ]

                    if not product_total.empty and product_total.iloc[0]["order_count"] > 0:
                        refund_rate = (
                            refund_count / product_total.iloc[0]["order_count"] * 100
                        )
                        total_revenue_product = float(product_total.iloc[0]["total_revenue"])
                    else:
                        refund_rate = 0.0
                        total_revenue_product = 0.0

                    top_refunded_products.append(
                        RefundedProductItem(
                            product_name=str(row["product_name"]) if pd.notna(row["product_name"]) else "Unknown",
                            refund_count=refund_count,
                            refund_rate=round(refund_rate, 1),
                            revenue=total_revenue_product,
                        )
                    )

            # Sort by refund count
            top_refunded_products.sort(key=lambda x: x.refund_count, reverse=True)
            top_refunded_products = top_refunded_products[:10]

            # === RETENTION METRICS ===
            # Filter to completed/paid orders only
            completed_df = df[df["orderStatus"].str.lower().isin(["paid", "completed"])]
            completed_df = completed_df[completed_df["customer_id"].notna() & (completed_df["customer_id"] != "")]

            total_customers = int(completed_df["customer_id"].nunique())
            total_revenue_customers = float(completed_df["total"].sum())

            if total_customers > 0:
                customer_orders = (
                    completed_df.groupby("customer_id").size().reset_index(name="order_count")
                )

                one_time = int((customer_orders["order_count"] == 1).sum())
                regular = int(
                    (customer_orders["order_count"] >= 2) & (customer_orders["order_count"] <= 3)
                ).sum()
                frequent = int((customer_orders["order_count"] >= 4).sum())

                returning_customers = regular + frequent
                retention_rate = (returning_customers / total_customers * 100) if total_customers > 0 else 0
                avg_ltv = (total_revenue_customers / total_customers) if total_customers > 0 else 0
            else:
                one_time = 0
                regular = 0
                frequent = 0
                retention_rate = 0.0
                avg_ltv = 0.0

            retention_metrics = RetentionMetrics(
                total_customers=total_customers,
                retention_rate=round(retention_rate, 1),
                avg_customer_lifetime_value=round(avg_ltv, 2),
                one_time_customer_pct=round((one_time / total_customers * 100) if total_customers > 0 else 0, 1),
                frequent_customer_pct=round((frequent / total_customers * 100) if total_customers > 0 else 0, 1),
            )

            # === GENERATE RECOMMENDATIONS ===
            recommendations = _generate_recommendations(
                top_revenue_leaks,
                top_bottlenecks,
                top_refunded_products,
                retention_metrics,
            )

            # Count critical issues
            critical_issues = sum(
                1 for leak in top_revenue_leaks if leak.severity == "high"
            ) + sum(
                1 for bn in top_bottlenecks if bn.severity == "high"
            ) + sum(
                1 for prod in top_refunded_products if prod.refund_rate > 15
            )

            insights_count = len(recommendations)

            logger.info(
                f"Insights dashboard complete: {insights_count} insights, {critical_issues} critical issues"
            )

            return InsightsDashboardResponse(
                total_orders=total_orders,
                total_revenue=total_revenue,
                total_leak_revenue=total_leak_revenue,
                leak_rate=round(leak_rate, 1),
                top_revenue_leaks=top_revenue_leaks,
                top_bottlenecks=top_bottlenecks,
                top_refunded_products=top_refunded_products,
                retention_metrics=retention_metrics,
                recommendations=recommendations,
                insights_count=insights_count,
                critical_issues=critical_issues,
            )

    except Exception as e:
        logger.error(f"Failed to calculate insights dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate insights")