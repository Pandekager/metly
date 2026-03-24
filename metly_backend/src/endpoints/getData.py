from fastapi import FastAPI, HTTPException, Query, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import os
from typing import List, Optional
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from uuid import UUID
import pandas as pd
import datetime
from passlib.context import CryptContext

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# src/endpoints/getData.py

# Attempt relative import of connectDB used in the project
try:
    from ..scripts.db.populateDB import connectDB
except Exception as e:
    logger.error(f"Failed to import connectDB: {e}")
    connectDB = None  # will raise later if not available

# Import customer analytics router
from .customerAnalytics import router as customer_analytics_router
from .shopify import router as shopify_router

app = FastAPI(title="Metly - Forecasts endpoint")

# Include routers
app.include_router(customer_analytics_router)
app.include_router(shopify_router)

# Globals populated at startup
conn = None
df_users = None
JWT_SECRET = None
JWT_ALGORITHM = None

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def initialize_app():
    """Initialize database connection and environment variables."""
    global conn, df_users, JWT_SECRET, JWT_ALGORITHM

    # Try to load from .env file first, but don't fail if it doesn't exist
    try:
        load_dotenv("./.env")
        logger.info("Loaded environment from .env file")
    except Exception as e:
        logger.warning(
            f"Could not load .env file: {e}. Will use system environment variables."
        )

    db_usr = os.getenv("DB_USR")
    db_pwd = os.getenv("DB_PWD")
    JWT_SECRET = os.getenv("JWT_SECRET")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

    logger.info(
        f"Initializing with DB_USR: {db_usr[:3] if db_usr else 'None'}*** (masked)"
    )
    logger.info(f"JWT_SECRET present: {JWT_SECRET is not None}")
    logger.info(f"JWT_ALGORITHM: {JWT_ALGORITHM}")

    if not db_usr or not db_pwd:
        logger.error("Database credentials not found in environment variables")
        raise RuntimeError(
            "DB_USR and DB_PWD must be set in environment variables or .env file"
        )

    if connectDB is None:
        logger.error("connectDB function not found")
        raise RuntimeError(
            "connectDB function not found. Ensure project db module exports connectDB"
        )

    try:
        logger.info("Attempting to connect to database...")
        conn, df_users = connectDB(db_usr, db_pwd)
        logger.info(
            f"Database connection successful. Users loaded: {len(df_users) if df_users is not None else 0}"
        )
    except Exception as e:
        logger.error(f"Failed to connect to DB: {e}", exc_info=True)
        raise RuntimeError(f"Failed to connect to DB: {e}")


# Initialize immediately on import
try:
    initialize_app()
except Exception as e:
    logger.error(f"Application initialization failed: {e}", exc_info=True)
    raise


class Forecast(BaseModel):
    date: str
    amount: float
    is_forecast: bool
    subcategory_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    platform: str


class LoginResponse(BaseModel):
    user_id: UUID


class BusinessAdviceResponse(BaseModel):
    response_text: str


def validate_user_access(user_to_query: UUID, current_user: UUID) -> None:
    """
    Validate that the authenticated user can access data for the requested user.

    Args:
        user_to_query: UUID of the user whose data is being requested
        current_user: UUID of the authenticated user

    Raises:
        HTTPException: If validation fails
    """
    # Security check: user can only query their own data
    if user_to_query != current_user:
        logger.warning(
            f"User {current_user} attempted to access data for {user_to_query}"
        )
        raise HTTPException(
            status_code=403, detail="Forbidden: cannot query other users"
        )

    # Check that user exists in df_users
    try:
        if df_users is None or df_users.empty:
            logger.error("User lookup unavailable - df_users is None or empty")
            raise HTTPException(status_code=500, detail="User lookup unavailable")

        if "id" not in df_users.columns:
            logger.error(
                f"df_users missing 'id' column. Available: {df_users.columns.tolist()}"
            )
            raise HTTPException(status_code=500, detail="User lookup unavailable")

        if str(user_to_query) not in df_users["id"].astype(str).values:
            logger.warning(f"Unauthorized user_id: {user_to_query}")
            raise HTTPException(status_code=401, detail="Unauthorized user_id")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking user authorization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error checking user authorization")


def refresh_users_cache() -> None:
    global df_users

    if conn is None or not hasattr(conn, "_sqlalchemy_engine"):
        logger.warning("Skipping user cache refresh due to missing DB engine")
        return

    sql = text(
        """
        SELECT u.*, p.name AS platform_name
        FROM users u
        JOIN platforms p ON u.platform_id = p.id
        """
    )
    df_users = pd.read_sql_query(sql, conn._sqlalchemy_engine)


def _get_admin_engine():
    load_dotenv("./.env")
    admin_usr = os.getenv("DB_USR_ADMIN")
    admin_pwd = os.getenv("DB_PWD_ADMIN")

    if not admin_usr or not admin_pwd:
        logger.error("Admin database credentials not configured")
        raise HTTPException(
            status_code=500,
            detail="Admin database credentials are not configured",
        )

    admin_conn, _ = connectDB(admin_usr, admin_pwd)
    if admin_conn is None or not hasattr(admin_conn, "_sqlalchemy_engine"):
        logger.error("Admin database connection unavailable")
        raise HTTPException(
            status_code=500,
            detail="Admin database connection unavailable",
        )

    return admin_conn, admin_conn._sqlalchemy_engine


def _normalize_platform_name(platform: str) -> str:
    normalized = (platform or "").strip().lower()
    mapping = {
        "shopify": "Shopify",
        "dandomain": "Dandomain Modern",
        "dandomain modern": "Dandomain Modern",
        "dandomain classic": "Dandomain Classic",
    }
    if normalized not in mapping:
        raise HTTPException(status_code=400, detail="Unsupported webshop platform")
    return mapping[normalized]


def _ensure_platform_id(platform_name: str) -> str:
    select_sql = text("SELECT id FROM platforms WHERE LOWER(name) = LOWER(:name) LIMIT 1")
    admin_conn, engine = _get_admin_engine()

    try:
        with engine.connect() as db_conn:
            existing = db_conn.execute(select_sql, {"name": platform_name}).fetchone()
            if existing:
                return str(existing[0])
    finally:
        try:
            admin_conn.close()
        except Exception:
            pass

    raise HTTPException(status_code=500, detail="Platform is not configured in the database")


def resolve_user_id(user_id: Optional[UUID], current_user: UUID) -> UUID:
    """
    Resolve the user_id to query, defaulting to current_user if not provided.

    Args:
        user_id: Optional UUID provided in the request
        current_user: UUID of the authenticated user

    Returns:
        UUID: The resolved user ID to query
    """
    return user_id or current_user


@app.on_event("startup")
def startup_event():
    """Startup event - initialization already done on import."""
    logger.info("Application startup event triggered")
    if conn is None:
        logger.error("Connection is None after initialization!")
        raise RuntimeError(
            "Database connection was not established during initialization"
        )


@app.on_event("shutdown")
def shutdown_event():
    """Close the database connection on shutdown."""
    global conn
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass


def _require_jose():
    try:
        from jose import jwt, JWTError  # type: ignore

        return jwt, JWTError
    except Exception as exc:
        raise RuntimeError(
            "Missing dependency 'python-jose'. Install with: pip install 'python-jose[cryptography]'"
        ) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Validate the Bearer JWT and return the subject as a UUID."""
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


@app.post("/auth/login", response_model=LoginResponse)
def login_user(credentials: LoginRequest):
    """
    Validate user credentials and return the user_id if valid.
    Uses bcrypt to securely verify password hashes.
    """
    logger.info(f"Login attempt for email: {credentials.email}")

    sql = text(
        "SELECT u.id, u.username, u.password FROM metlydk_main.users u WHERE u.username = :email"
    )
    try:
        if conn is None or not hasattr(conn, "_sqlalchemy_engine"):
            logger.error("No database connection available for login.")
            raise HTTPException(
                status_code=500, detail="Database connection unavailable."
            )
        # Use SQLAlchemy engine attached to connection for proper parameterized queries
        with conn._sqlalchemy_engine.connect() as db_conn:
            result = db_conn.execute(sql, {"email": credentials.email}).fetchone()

        if not result:
            logger.warning(f"User not found: {credentials.email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Access Row object using index
        user_id = result[0]  # id is first column
        db_password = result[2]  # password is third column

        logger.info(f"User found: {credentials.email}, user_id: {user_id}")
        logger.debug(
            f"Password hash starts with: {db_password[:10] if db_password else 'None'}"
        )

        # Check if password is hashed (bcrypt hashes start with $2b$)
        if not db_password or not db_password.startswith("$2b$"):
            logger.error(
                f"Password not hashed for user {credentials.email}! Run migration script."
            )
            raise HTTPException(
                status_code=500,
                detail="Server configuration error. Please contact administrator.",
            )

        # Truncate password to 72 bytes (bcrypt limitation)
        password = credentials.password[:72]

        # Verify password hash
        try:
            if not pwd_context.verify(password, db_password):
                logger.warning(
                    f"Password verification failed for user: {credentials.email}"
                )
                raise HTTPException(status_code=401, detail="Invalid email or password")
        except Exception as e:
            # If verification fails due to bcrypt error, return generic error
            logger.error(f"Password verification error for {credentials.email}: {e}")
            raise HTTPException(status_code=401, detail="Invalid email or password")

        logger.info(f"Login successful for user: {credentials.email}")
        return {"user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {credentials.email}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")


@app.post("/auth/register", response_model=LoginResponse)
def register_user(payload: RegisterRequest):
    logger.info("Registration attempt for email: %s", payload.email)

    if len(payload.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long",
        )

    platform_name = _normalize_platform_name(payload.platform)
    platform_id = _ensure_platform_id(platform_name)

    existing_user_sql = text(
        "SELECT id FROM metlydk_main.users WHERE username = :email LIMIT 1"
    )
    create_user_sql = text(
        """
        INSERT INTO metlydk_main.users
        (id, username, password, created, platform_id, tenant, client_id, client_secret)
        VALUES(UUID(), :email, :password, current_timestamp(), :platform_id, NULL, NULL, NULL)
        """
    )
    lookup_user_sql = text(
        "SELECT id FROM metlydk_main.users WHERE username = :email LIMIT 1"
    )

    try:
        admin_conn, admin_engine = _get_admin_engine()

        with admin_engine.begin() as db_conn:
            existing = db_conn.execute(
                existing_user_sql, {"email": payload.email}
            ).fetchone()
            if existing:
                raise HTTPException(
                    status_code=409, detail="A user with this email already exists"
                )

            hashed_password = pwd_context.hash(payload.password[:72])
            db_conn.execute(
                create_user_sql,
                {
                    "email": payload.email,
                    "password": hashed_password,
                    "platform_id": platform_id,
                },
            )
            created_user = db_conn.execute(
                lookup_user_sql, {"email": payload.email}
            ).fetchone()

        if not created_user:
            raise HTTPException(status_code=500, detail="User creation failed")

        refresh_users_cache()

        logger.info("Registration successful for email: %s", payload.email)
        return {"user_id": created_user[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration error for %s: %s", payload.email, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Registration failed: {e}")
    finally:
        try:
            admin_conn.close()
        except Exception:
            pass


@app.get("/forecasts", response_model=List[Forecast])
def get_forecasts(
    user_id: Optional[UUID] = Query(
        None,
        description="UUID of the user to fetch forecasts for (optional; if omitted, token subject is used)",
    ),
    current_user: UUID = Depends(get_current_user),
):
    """
    Read-only endpoint returning forecasts for an authorized user.

    Authentication is performed with a Bearer JWT. The token's `sub` claim must
    contain the UUID of the requesting user. If `user_id` is provided it must
    match the authenticated user's UUID — this prevents a client from querying
    data for other users.
    """
    logger.info(f"Forecasts request from user: {current_user}")

    user_to_query = resolve_user_id(user_id, current_user)
    validate_user_access(user_to_query, current_user)

    logger.info(f"Fetching forecasts for user: {user_to_query}")

    # Safe parameterized query using SQLAlchemy text() with named parameter
    sql = text(
        "SELECT f.date, ROUND(f.amount) AS amount, f.is_forecast, f.subcategory_name "
        "FROM forecasts f "
        "INNER JOIN ( "
        "SELECT subcategory_name "
        "FROM forecasts "
        "WHERE user_id = :user_id "
        "AND date >= DATE_SUB(LAST_DAY(DATE_SUB(NOW(), INTERVAL 1 MONTH)), INTERVAL DAY(LAST_DAY(DATE_SUB(NOW(), INTERVAL 1 MONTH))) - 1 DAY) "
        "GROUP BY subcategory_name "
        "HAVING SUM(amount) > 0 "
        "    ) AS valid_subcategories ON f.subcategory_name = valid_subcategories.subcategory_name "
        "WHERE user_id = :user_id "
        "AND f.date >= DATE_SUB(LAST_DAY(DATE_SUB(NOW(), INTERVAL 1 MONTH)), INTERVAL DAY(LAST_DAY(DATE_SUB(NOW(), INTERVAL 1 MONTH))) - 1 DAY) "
    )
    try:
        if conn is None or not hasattr(conn, "_sqlalchemy_engine"):
            logger.error("No database connection available for forecasts.")
            raise HTTPException(
                status_code=500, detail="Database connection unavailable."
            )
        result = pd.read_sql_query(
            sql, conn._sqlalchemy_engine, params={"user_id": str(user_to_query)}
        )
        result = result.fillna("").map(
            lambda v: (
                v.isoformat()
                if isinstance(v, (pd.Timestamp, datetime.date, datetime.datetime))
                else str(v)
            )
        )
        rows = result.to_dict(orient="records")
        logger.info(f"Returning {len(rows)} forecast records for user {user_to_query}")
    except Exception as e:
        logger.error(
            f"Database query failed for user {user_to_query}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")

    return rows


@app.get("/forecast_business_advice", response_model=BusinessAdviceResponse)
def get_business_advice(
    user_id: Optional[UUID] = Query(
        None,
        description="UUID of the user to fetch business advice for (optional; if omitted, token subject is used)",
    ),
    current_user: UUID = Depends(get_current_user),
):
    """
    Read-only endpoint returning AI-generated business advice for an authorized user.

    Authentication is performed with a Bearer JWT. The token's `sub` claim must
    contain the UUID of the requesting user. If `user_id` is provided it must
    match the authenticated user's UUID — this prevents a client from querying
    data for other users.
    """
    logger.info(f"Business advice request from user: {current_user}")

    user_to_query = resolve_user_id(user_id, current_user)
    validate_user_access(user_to_query, current_user)

    logger.info(f"Fetching business advice for user: {user_to_query}")

    # Safe parameterized query using SQLAlchemy text() with named parameter
    sql = text(
        "SELECT response_text FROM metlydk_main.ai_responses "
        "WHERE ai_category_id = 'forecast_business_advice' "
        "AND user_id = :user_id "
        "ORDER BY created DESC "
        "LIMIT 1"
    )

    try:
        if conn is None or not hasattr(conn, "_sqlalchemy_engine"):
            logger.error("No database connection available for business advice.")
            raise HTTPException(
                status_code=500, detail="Database connection unavailable."
            )

        with conn._sqlalchemy_engine.connect() as db_conn:
            result = db_conn.execute(sql, {"user_id": str(user_to_query)}).fetchone()

        if not result:
            logger.warning(f"No business advice found for user: {user_to_query}")
            raise HTTPException(
                status_code=404,
                detail="No business advice available. Please generate forecasts first.",
            )

        response_text = result[0]
        logger.info(
            f"Returning business advice for user {user_to_query} ({len(response_text)} characters)"
        )

        return {"response_text": response_text}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Database query failed for user {user_to_query}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")


# To host the app, use:
# uvicorn src.endpoints.getData:app --host 0.0.0.0 --port 8000
