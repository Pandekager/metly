from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List
from uuid import UUID
import logging
import os
from sqlalchemy import text
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

from src.scripts.db.populateDB import connectDB

logger = logging.getLogger(__name__)

router = APIRouter()

security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    try:
        if JWT_SECRET is None:
            raise HTTPException(status_code=500, detail="JWT_SECRET not configured")
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


class ProductAnalytics(BaseModel):
    product_id: str
    product_name: str
    subcategory_name: str
    units_sold: int
    total_revenue: float
    order_count: int


class ProductTrend(BaseModel):
    product_name: str
    month: str
    units_sold: int
    revenue: float


class ProductAnalyticsResponse(BaseModel):
    top_products: List[ProductAnalytics]
    sales_trends: List[ProductTrend]


class BusinessAdviceResponse(BaseModel):
    response_text: str


@router.get("/product_analytics", response_model=ProductAnalyticsResponse)
def get_product_analytics(current_user: UUID = Depends(get_current_user)):
    load_dotenv("./.env")
    db_usr = os.getenv("DB_USR")
    db_pwd = os.getenv("DB_PWD")

    if not db_usr or not db_pwd:
        raise HTTPException(status_code=500, detail="Database configuration error")

    conn, _ = connectDB(db_usr, db_pwd)
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        # Query for top products
        products_sql = text("""
            SELECT
                p.id AS product_id,
                p.product_name,
                p.subcategory_name,
                COALESCE(SUM(ol.amount), 0) AS units_sold,
                COALESCE(SUM(ol.unit_revenue * ol.amount), 0) AS total_revenue,
                COUNT(DISTINCT ol.order_id) AS order_count
            FROM products p
            LEFT JOIN order_lines ol ON p.id = ol.product_id
            WHERE p.user_id = :user_id
            GROUP BY p.id, p.product_name, p.subcategory_name
            HAVING SUM(ol.amount) > 0
            ORDER BY total_revenue DESC
            LIMIT 50
        """)

        # Query for monthly trends per product
        trends_sql = text("""
            SELECT
                p.product_name,
                DATE_FORMAT(o.created, '%Y-%m') AS month,
                SUM(ol.amount) AS units_sold,
                SUM(ol.unit_revenue * ol.amount) AS revenue
            FROM products p
            JOIN order_lines ol ON p.id = ol.product_id
            JOIN orders o ON ol.order_id = o.id
            WHERE p.user_id = :user_id
                AND o.created >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
            GROUP BY p.id, p.product_name, month
            ORDER BY p.product_name, month
        """)

        top_products = []
        sales_trends = []

        with conn._sqlalchemy_engine.connect() as db_conn:
            # Get top products
            products_result = db_conn.execute(
                products_sql, {"user_id": str(current_user)}
            )
            for row in products_result:
                top_products.append(
                    ProductAnalytics(
                        product_id=str(row[0]),
                        product_name=row[1] or "",
                        subcategory_name=row[2] or "",
                        units_sold=int(row[3]),
                        total_revenue=float(row[4]),
                        order_count=int(row[5]),
                    )
                )

            # Get sales trends
            trends_result = db_conn.execute(trends_sql, {"user_id": str(current_user)})
            for row in trends_result:
                sales_trends.append(
                    ProductTrend(
                        product_name=row[0] or "",
                        month=row[1] or "",
                        units_sold=int(row[2]),
                        revenue=float(row[3]),
                    )
                )

        logger.info(
            f"Returning {len(top_products)} products and {len(sales_trends)} trends for user {current_user}"
        )
        return {"top_products": top_products, "sales_trends": sales_trends}

    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/product_business_advice", response_model=BusinessAdviceResponse)
def get_product_business_advice(
    user_id: UUID = Query(
        None,
        description="UUID of the user to fetch business advice for (optional; if omitted, token subject is used)",
    ),
    current_user: UUID = Depends(get_current_user),
):
    """
    Read-only endpoint returning AI-generated product business advice for an authorized user.
    """
    load_dotenv("./.env")
    db_usr = os.getenv("DB_USR")
    db_pwd = os.getenv("DB_PWD")

    if not db_usr or not db_pwd:
        raise HTTPException(status_code=500, detail="Database configuration error")

    # Resolve user_id (default to current_user if not provided)
    user_to_query = user_id or current_user

    # Validate access
    if user_to_query != current_user:
        logger.warning(
            f"User {current_user} attempted to access data for {user_to_query}"
        )
        raise HTTPException(
            status_code=403, detail="Forbidden: cannot query other users"
        )

    conn, _ = connectDB(db_usr, db_pwd)
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        # Safe parameterized query using SQLAlchemy text() with named parameter
        sql = text(
            "SELECT response_text FROM ai_responses "
            "WHERE ai_category_id = 'product_business_advice' "
            "AND user_id = :user_id "
            "ORDER BY created DESC "
            "LIMIT 1"
        )

        with conn._sqlalchemy_engine.connect() as db_conn:
            result = db_conn.execute(sql, {"user_id": str(user_to_query)}).fetchone()

        if not result:
            logger.info(
                f"No product business advice found yet for user: {user_to_query}"
            )
            return {"response_text": ""}

        response_text = result[0]
        logger.info(
            f"Returning product business advice for user {user_to_query} ({len(response_text)} characters)"
        )

        return {"response_text": response_text}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database query failed for user {user_to_query}: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")
    finally:
        conn.close()
