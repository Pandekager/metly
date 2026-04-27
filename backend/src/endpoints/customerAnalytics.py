from fastapi import APIRouter, Depends, HTTPException
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

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
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

CITY_COORDINATES = {
    "København": (55.6761, 12.5683),
    "Aarhus": (56.1629, 10.2039),
    "Odense": (55.4030, 10.3834),
    "Aalborg": (57.0476, 9.9256),
    "Esbjerg": (55.4898, 8.4516),
    "Randers": (56.4599, 10.0379),
    "Kolding": (55.4918, 9.4690),
    "Horsens": (55.8629, 9.8509),
    "Vejle": (55.7094, 9.5357),
    "Roskilde": (55.6421, 12.0849),
    "Herning": (56.1396, 8.9738),
    "Silkeborg": (56.1693, 9.7958),
    "Næstved": (55.2298, 11.7606),
    "Fredericia": (55.6039, 9.7528),
    "Viborg": (56.4500, 9.4000),
    # Alternative spellings
    "Copenhagen": (55.6761, 12.5683),
}

class CityAnalytics(BaseModel):
    city: str
    customer_count: int
    revenue: float
    latitude: float
    longitude: float

class AnalyticsResponse(BaseModel):
    data: List[CityAnalytics]

@router.get("/customer_analytics", response_model=AnalyticsResponse)
def get_customer_analytics(current_user: UUID = Depends(get_current_user)):
    load_dotenv("./.env")
    db_usr = os.getenv("DB_USR")
    db_pwd = os.getenv("DB_PWD")
    
    if not db_usr or not db_pwd:
        raise HTTPException(status_code=500, detail="Database configuration error")
    
    conn, _ = connectDB(db_usr, db_pwd)
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        sql = text("""
            SELECT 
                c.billing_city AS city,
                COUNT(DISTINCT c.id) AS customer_count,
                COALESCE(SUM(o.total), 0) AS revenue
            FROM customers c
            LEFT JOIN orders o ON c.id = o.customer_id AND o.orderStatus = 'completed'
            WHERE c.user_id = :user_id
                AND c.billing_city IS NOT NULL 
                AND c.billing_city != ''
            GROUP BY c.billing_city
            ORDER BY customer_count DESC
            LIMIT 20
        """)
        
        with conn._sqlalchemy_engine.connect() as db_conn:
            result = db_conn.execute(sql, {"user_id": str(current_user)})
            rows = result.fetchall()
            
            analytics_data = []
            for row in rows:
                city = row[0]
                customer_count = int(row[1])
                revenue = float(row[2])
                lat, lng = CITY_COORDINATES.get(city, (0.0, 0.0))
                
                analytics_data.append(CityAnalytics(
                    city=city,
                    customer_count=customer_count,
                    revenue=revenue,
                    latitude=lat,
                    longitude=lng
                ))
            
            return {"data": analytics_data}
            
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
