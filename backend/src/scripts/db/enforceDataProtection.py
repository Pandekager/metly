from __future__ import annotations

from dotenv import load_dotenv
import logging
import os

from src.scripts.db.populateDB import connectDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def enforce_data_protection(db_usr: str, db_pwd: str):
    load_dotenv("./.env")

    pii_retention_days = int(os.getenv("CUSTOMER_PII_RETENTION_DAYS", "30"))
    forecast_retention_days = int(os.getenv("AI_RESPONSE_RETENTION_DAYS", "180"))

    conn, _ = connectDB(db_usr, db_pwd)
    if conn is None:
        logger.warning("Data protection step skipped because DB connection is unavailable")
        return

    statements = [
        (
            """
            UPDATE customers
            SET billing_firstName = NULL,
                billing_lastName = NULL,
                billing_addressLine = NULL,
                billing_email = NULL,
                extended_internal = NULL,
                extended_external = NULL
            WHERE created < (UTC_TIMESTAMP() - INTERVAL %s DAY)
              AND (
                billing_firstName IS NOT NULL OR
                billing_lastName IS NOT NULL OR
                billing_addressLine IS NOT NULL OR
                billing_email IS NOT NULL OR
                extended_internal IS NOT NULL OR
                extended_external IS NOT NULL
              )
            """,
            (pii_retention_days,),
            "customers_pseudonymized",
        ),
        (
            """
            DELETE FROM ai_responses
            WHERE created < (UTC_TIMESTAMP() - INTERVAL %s DAY)
            """,
            (forecast_retention_days,),
            "expired_ai_responses_deleted",
        ),
    ]

    try:
        with conn.cursor() as cursor:
            for sql, params, label in statements:
                cursor.execute(sql, params)
                logger.info("%s=%s", label, cursor.rowcount)
        conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    load_dotenv("./.env")
    enforce_data_protection(
        os.getenv("DB_USR_ADMIN", ""),
        os.getenv("DB_PWD_ADMIN", ""),
    )
