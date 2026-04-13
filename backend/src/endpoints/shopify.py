import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Query
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import text
from uuid import UUID

from .auth import get_current_user
from src.integrations.shopify import (
    build_shopify_authorize_url,
    exchange_shopify_access_token,
    normalize_shop_domain,
    verify_shopify_hmac,
)
from src.scripts.analysis.consultAi import get_business_advice
from src.scripts.analysis.predictSales import predictSales
from src.scripts.db.populateDB import connectDB, populateDB


router = APIRouter(prefix="/integrations/shopify", tags=["shopify"])


class ShopifyInstallResponse(BaseModel):
    authorize_url: str
    state: str


class ShopifyConnectionStatus(BaseModel):
    connected: bool
    platform: str | None = None
    shop: str | None = None
    has_access_token: bool = False


class ShopifyCallbackResponse(BaseModel):
    success: bool
    shop: str


def _fetch_shopify_connection_state(engine, user_id: str):
    sql = text(
        """
        SELECT p.name AS platform_name, u.tenant, u.client_secret
        FROM users u
        LEFT JOIN platforms p ON u.platform_id = p.id
        WHERE u.id = :user_id
        LIMIT 1
        """
    )
    with engine.connect() as sql_conn:
        row = sql_conn.execute(sql, {"user_id": user_id}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    platform_name = row[0]
    tenant = row[1]
    access_token = row[2]
    has_access_token = bool(access_token)
    connected = platform_name == "Shopify" and bool(tenant) and has_access_token
    return {
        "platform_name": platform_name,
        "tenant": tenant,
        "has_access_token": has_access_token,
        "connected": connected,
    }


def _delete_user_and_related_data(engine, user_id: str):
    cleanup_statements = [
        text("DELETE FROM order_lines WHERE user_id = :user_id"),
        text("DELETE FROM orders WHERE user_id = :user_id"),
        text("DELETE FROM product_categories WHERE user_id = :user_id"),
        text("DELETE FROM products WHERE user_id = :user_id"),
        text("DELETE FROM customers WHERE user_id = :user_id"),
        text("DELETE FROM languages WHERE user_id = :user_id"),
        text("DELETE FROM forecasts WHERE user_id = :user_id"),
        text("DELETE FROM ai_responses WHERE user_id = :user_id"),
        text("DELETE FROM top_pairs WHERE user_id = :user_id"),
        text("DELETE FROM users WHERE id = :user_id"),
    ]
    with engine.begin() as sql_conn:
        for statement in cleanup_statements:
            sql_conn.execute(statement, {"user_id": user_id})


def _load_shopify_settings() -> tuple[str, str, str]:
    load_dotenv("./.env")
    api_key = os.getenv("SHOPIFY_API_KEY")
    api_secret = os.getenv("SHOPIFY_API_SECRET") or os.getenv("AHOPIFY_API_SECRET")
    scopes = os.getenv("SHOPIFY_SCOPES", "")

    if not api_key or not api_secret:
        raise HTTPException(
            status_code=500,
            detail="Shopify credentials are not configured in the backend environment",
        )

    return api_key, api_secret, scopes


def _require_backend_connection():
    load_dotenv("./.env")
    db_usr = os.getenv("DB_USR_ADMIN") or os.getenv("DB_USR")
    db_pwd = os.getenv("DB_PWD_ADMIN") or os.getenv("DB_PWD")
    db_conn, _ = connectDB(db_usr, db_pwd)
    if db_conn is None or not hasattr(db_conn, "_sqlalchemy_engine"):
        raise HTTPException(status_code=500, detail="Database connection unavailable")
    return db_conn, db_conn._sqlalchemy_engine


def _build_state_token(
    user_id: UUID, shop: str, secret: str, signup_flow: bool = False
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "shop": shop,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
        "purpose": "shopify-oauth",
        "signup_flow": signup_flow,
    }
    return jwt.encode(payload, secret, algorithm=os.getenv("JWT_ALGORITHM", "HS256"))


def _decode_state_token(state: str, secret: str) -> dict:
    try:
        payload = jwt.decode(state, secret, algorithms=[os.getenv("JWT_ALGORITHM", "HS256")])
    except JWTError as exc:
        raise HTTPException(status_code=400, detail="Invalid Shopify OAuth state") from exc

    if payload.get("purpose") != "shopify-oauth":
        raise HTTPException(status_code=400, detail="Invalid Shopify OAuth state")
    return payload


def _ensure_shopify_platform_id(engine) -> str:
    select_sql = text("SELECT id FROM platforms WHERE LOWER(name) = 'shopify' LIMIT 1")
    insert_sql = text("INSERT INTO platforms (name) VALUES ('Shopify')")

    with engine.begin() as db_conn:
        existing = db_conn.execute(select_sql).fetchone()
        if existing:
            return str(existing[0])

        try:
            db_conn.execute(insert_sql)
        except Exception:
            # Another request may have inserted the row in the meantime.
            pass

        existing = db_conn.execute(select_sql).fetchone()
        if not existing:
            raise HTTPException(status_code=500, detail="Unable to provision Shopify platform")
        return str(existing[0])


@router.get("/status", response_model=ShopifyConnectionStatus)
def shopify_status(current_user: UUID = Depends(get_current_user)):
    raw_conn, engine = _require_backend_connection()
    state = _fetch_shopify_connection_state(engine, str(current_user))
    try:
        raw_conn.close()
    except Exception:
        pass

    return ShopifyConnectionStatus(
        connected=state["connected"],
        platform=state["platform_name"],
        shop=state["tenant"] if state["tenant"] else None,
        has_access_token=state["has_access_token"],
    )


@router.get("/install", response_model=ShopifyInstallResponse)
def shopify_install(
    shop: str = Query(..., description="Shopify shop domain"),
    redirect_uri: str = Query(..., description="Public callback URL"),
    signup: bool = Query(False, description="Whether this install is part of signup"),
    current_user: UUID = Depends(get_current_user),
):
    api_key, _, scopes = _load_shopify_settings()
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        raise HTTPException(status_code=500, detail="JWT secret not configured")

    normalized_shop = normalize_shop_domain(shop)
    state = _build_state_token(
        current_user, normalized_shop, jwt_secret, signup_flow=signup
    )
    authorize_url = build_shopify_authorize_url(
        normalized_shop,
        api_key,
        scopes,
        redirect_uri,
        state,
    )
    return ShopifyInstallResponse(authorize_url=authorize_url, state=state)


@router.get("/callback", response_model=ShopifyCallbackResponse)
def shopify_callback(
    code: str = Query(...),
    hmac: str = Query(...),
    shop: str = Query(...),
    state: str = Query(...),
    host: str | None = Query(None),
    timestamp: str | None = Query(None),
):
    api_key, api_secret, _ = _load_shopify_settings()
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        raise HTTPException(status_code=500, detail="JWT secret not configured")

    normalized_shop = normalize_shop_domain(shop)
    params = {"code": code, "hmac": hmac, "shop": normalized_shop, "state": state}
    if host is not None:
        params["host"] = host
    if timestamp is not None:
        params["timestamp"] = timestamp

    if not verify_shopify_hmac(params, api_secret):
        raise HTTPException(status_code=400, detail="Invalid Shopify callback signature")

    state_payload = _decode_state_token(state, jwt_secret)
    if state_payload.get("shop") != normalized_shop:
        raise HTTPException(status_code=400, detail="Shopify OAuth state mismatch")

    raw_conn, engine = _require_backend_connection()
    signup_flow = bool(state_payload.get("signup_flow"))

    try:
        token_payload = exchange_shopify_access_token(
            normalized_shop,
            api_key,
            api_secret,
            code,
        )
        access_token = token_payload.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=500, detail="Shopify access token exchange failed"
            )

        platform_id = _ensure_shopify_platform_id(engine)

        update_sql = text(
            """
            UPDATE users
            SET platform_id = :platform_id,
                tenant = :tenant,
                client_id = :client_id,
                client_secret = :client_secret
            WHERE id = :user_id
            """
        )

        with engine.begin() as sql_conn:
            result = sql_conn.execute(
                update_sql,
                {
                    "platform_id": platform_id,
                    "tenant": normalized_shop,
                    "client_id": api_key,
                    "client_secret": access_token,
                    "user_id": state_payload["sub"],
                },
            )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")

        state = _fetch_shopify_connection_state(engine, state_payload["sub"])
        if not state["connected"] or state["tenant"] != normalized_shop:
            raise HTTPException(
                status_code=500,
                detail="Shopify connection was not persisted correctly in the database",
            )

        load_dotenv("./.env")
        db_usr = os.getenv("DB_USR_ADMIN")
        db_pwd = os.getenv("DB_PWD_ADMIN")
        populateDB(
            db_usr,
            db_pwd,
            user_ids=[state_payload["sub"]],
            raise_on_error=True,
        )
        predictSales(
            db_usr,
            db_pwd,
            user_ids=[state_payload["sub"]],
        )
        get_business_advice(
            db_usr,
            db_pwd,
            user_ids=[state_payload["sub"]],
        )

        return ShopifyCallbackResponse(success=True, shop=normalized_shop)
    except HTTPException:
        if signup_flow:
            _delete_user_and_related_data(engine, state_payload["sub"])
        raise
    except Exception as exc:
        if signup_flow:
            _delete_user_and_related_data(engine, state_payload["sub"])
        message = str(exc)
        if (
            "not approved to access the Order object" in message
            or "protected-customer-data" in message
            or "ACCESS_DENIED" in message
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Shopify denied order access for this app. "
                    "The app needs protected customer data approval before Metly can import orders."
                ),
            )
        raise
    finally:
        try:
            raw_conn.close()
        except Exception:
            pass
