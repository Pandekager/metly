from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List
from uuid import UUID
import logging
import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
import pymysql
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

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
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return UUID(user_id)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token")


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
    db_host = os.getenv("DB_HOST", "metly.dk")

    if not db_usr or not db_pwd:
        raise HTTPException(status_code=500, detail="Database configuration error")

    try:
        conn = pymysql.connect(
            host=db_host,
            user=db_usr,
            password=db_pwd,
            database="metlydk_main",
            cursorclass=pymysql.cursors.DictCursor,
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        user_id_str = str(current_user)

        with conn.cursor() as cursor:
            # Get products with sales data
            products_sql = """
                SELECT 
                    p.id AS product_id,
                    p.product_name,
                    p.subcategory_name,
                    COALESCE(ol.total_units, 0) AS units_sold,
                    COALESCE(ol.total_revenue, 0) AS total_revenue,
                    COALESCE(ol.order_count, 0) AS order_count
                FROM products p
                LEFT JOIN (
                    SELECT 
                        product_id,
                        SUM(amount) AS total_units,
                        SUM(unit_revenue * amount) AS total_revenue,
                        COUNT(DISTINCT order_id) AS order_count
                    FROM order_lines
                    WHERE user_id = %s
                    GROUP BY product_id
                ) ol ON p.id = ol.product_id
                WHERE p.user_id = %s
                    AND ol.total_units > 0
                ORDER BY ol.total_revenue DESC
                LIMIT 50
            """
            cursor.execute(products_sql, (user_id_str, user_id_str))
            products = cursor.fetchall()

            top_products = [
                ProductAnalytics(
                    product_id=str(p["product_id"]),
                    product_name=p["product_name"] or "",
                    subcategory_name=p["subcategory_name"] or "",
                    units_sold=int(p["units_sold"]) if p["units_sold"] else 0,
                    total_revenue=float(p["total_revenue"])
                    if p["total_revenue"]
                    else 0.0,
                    order_count=int(p["order_count"]) if p["order_count"] else 0,
                )
                for p in products
            ]

            # Get monthly trends
            trends_sql = """
                SELECT 
                    DATE_FORMAT(o.created, '%%Y-%%m') AS month,
                    SUM(ol.amount) AS units_sold,
                    SUM(ol.unit_revenue * ol.amount) AS revenue
                FROM order_lines ol
                JOIN orders o ON ol.order_id = o.id
                WHERE ol.user_id = %s
                    AND o.created >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
                GROUP BY month
                ORDER BY month
            """
            cursor.execute(trends_sql, (user_id_str,))
            trends = cursor.fetchall()

            sales_trends = [
                ProductTrend(
                    product_name="Overall",
                    month=t["month"] or "",
                    units_sold=int(t["units_sold"]) if t["units_sold"] else 0,
                    revenue=float(t["revenue"]) if t["revenue"] else 0.0,
                )
                for t in trends
            ]

        conn.close()
        logger.info(
            f"Returning {len(top_products)} products, {len(sales_trends)} trends"
        )
        return {"top_products": top_products, "sales_trends": sales_trends}

    except Exception as e:
        logger.error(f"Error: {e}")
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/product_business_advice", response_model=BusinessAdviceResponse)
def get_product_business_advice(
    user_id: UUID = Query(
        None,
        description="UUID of the user to fetch business advice for (optional; if omitted, token subject is used)",
    ),
    current_user: UUID = Depends(get_current_user),
):
    load_dotenv("./.env")
    db_usr = os.getenv("DB_USR")
    db_pwd = os.getenv("DB_PWD")
    db_host = os.getenv("DB_HOST", "metly.dk")

    if not db_usr or not db_pwd:
        raise HTTPException(status_code=500, detail="Database configuration error")

    user_to_query = user_id or current_user

    if user_to_query != current_user:
        logger.warning(
            f"User {current_user} attempted to access data for {user_to_query}"
        )
        raise HTTPException(
            status_code=403, detail="Forbidden: cannot query other users"
        )

    try:
        conn = pymysql.connect(
            host=db_host,
            user=db_usr,
            password=db_pwd,
            database="metlydk_main",
            cursorclass=pymysql.cursors.DictCursor,
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        user_id_str = str(user_to_query)

        with conn.cursor() as cursor:
            sql = """
                SELECT response_text FROM ai_responses 
                WHERE ai_category_id = 'product_business_advice' 
                AND user_id = %s
                ORDER BY created DESC 
                LIMIT 1
            """
            cursor.execute(sql, (user_id_str,))
            result = cursor.fetchone()

        conn.close()

        if result:
            return {"response_text": result["response_text"]}
        else:
            return {
                "response_text": "Ingen produktanalyse tilgængelig endnu. Kør produktanalyse for at få AI-anbefalinger."
            }

    except Exception as e:
        logger.error(f"Error: {e}")
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))
