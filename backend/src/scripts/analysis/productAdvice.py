import pandas as pd
import logging
import json
from datetime import datetime
import os
from dotenv import load_dotenv

from src.scripts.db.populateDB import connectDB

try:
    import google.generativeai as genai
except Exception as exc:
    genai = None
    _GENAI_IMPORT_ERROR = exc
else:
    _GENAI_IMPORT_ERROR = None

# Load environment variables
load_dotenv("./.env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_product_advice(db_usr, db_pwd, user_ids=None):
    """
    Fetch product sales data for users, send to Gemini AI for business advice,
    and save the response to the database.

    Args:
        db_usr: Database username
        db_pwd: Database password
        user_ids: Optional list of user IDs to process

    Returns:
        dict: Response containing AI advice and status
    """
    conn = None
    cursor = None

    try:
        # Connect to database
        conn, df_users = connectDB(db_usr, db_pwd)
        if conn is None:
            logger.error("Failed to connect to database")
            return {"error": "Database connection failed"}

        # Loop over users
        if user_ids:
            allowed_user_ids = {str(user_id) for user_id in user_ids}
            df_users = df_users[
                df_users["id"].astype(str).isin(allowed_user_ids)
            ].copy()

        for _, user in df_users.iterrows():
            # Query product sales data
            query = """
            SELECT 
                p.id AS product_id,
                p.product_name,
                p.subcategory_name,
                p.maincategory_name,
                SUM(ol.amount) AS units_sold,
                SUM(ol.unit_revenue * ol.amount) AS total_revenue,
                COUNT(DISTINCT ol.order_id) AS order_count
            FROM products p
            JOIN order_lines ol ON p.id = ol.product_id
            JOIN orders o ON ol.order_id = o.id
            WHERE p.user_id = %s
            GROUP BY p.id, p.product_name, p.subcategory_name, p.maincategory_name
            ORDER BY total_revenue DESC
            """

            cursor = conn.cursor()
            cursor.execute(query, (user["id"],))
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(results, columns=columns)

            if df.empty:
                logger.warning(f"No product sales data found for user {user['id']}")
                continue

            logger.info(f"Retrieved {len(df)} product records for user {user['id']}")

            # Prepare data summary for AI
            data_summary = prepare_product_summary(df)

            # Call Gemini AI
            ai_response = call_gemini_product_ai(data_summary)

            if "error" in ai_response:
                return ai_response

            # Save AI response to database
            response_text = ai_response.get("advice", "")
            save_ai_response(conn, user["id"], response_text)

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error in get_product_advice: {str(e)}")
        return {"error": str(e)}

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def prepare_product_summary(df: pd.DataFrame) -> str:
    """
    Prepare a concise summary of the product sales data for the AI.

    Args:
        df: DataFrame with product sales data

    Returns:
        str: Formatted data summary
    """
    # Calculate metrics
    total_units = df["units_sold"].sum() if "units_sold" in df.columns else 0
    total_revenue = df["total_revenue"].sum() if "total_revenue" in df.columns else 0
    total_orders = df["order_count"].sum() if "order_count" in df.columns else 0
    num_products = len(df)

    summary = "# Produkt Sales Data Analysis\n\n"

    # Overview
    summary += f"## Overview:\n"
    summary += f"- Total products: {num_products}\n"
    summary += f"- Total units sold: {int(total_units)}\n"
    summary += f"- Total revenue: {int(total_revenue)} DKK\n"
    summary += f"- Total orders: {int(total_orders)}\n"

    # Top selling products
    summary += f"\n## Top Selling Products (by revenue):\n"
    top_products = df.head(10)
    for _, row in top_products.iterrows():
        name = row.get("product_name", "Unknown")
        category = row.get("subcategory_name", "Unknown")
        units = int(row.get("units_sold", 0))
        revenue = int(row.get("total_revenue", 0))
        orders = int(row.get("order_count", 0))
        summary += f"- {name} ({category}): {units} units, {revenue} DKK revenue, {orders} orders\n"

    # Category performance
    if "subcategory_name" in df.columns and "total_revenue" in df.columns:
        summary += f"\n## Category Performance:\n"
        category_totals = (
            df.groupby("subcategory_name")
            .agg({"units_sold": "sum", "total_revenue": "sum", "order_count": "sum"})
            .sort_values("total_revenue", ascending=False)
        )
        for cat, row in category_totals.iterrows():
            summary += f"- {cat}: {int(row['units_sold'])} units, {int(row['total_revenue'])} DKK\n"

    # Slow-moving products (low sales relative to others)
    if len(df) > 5:
        summary += f"\n## Slow-Moving Products (bottom 5 by units sold):\n"
        slow_products = df.nsmallest(5, "units_sold")
        for _, row in slow_products.iterrows():
            name = row.get("product_name", "Unknown")
            units = int(row.get("units_sold", 0))
            revenue = int(row.get("total_revenue", 0))
            summary += f"- {name}: {units} units, {revenue} DKK\n"

    # Detailed data (limited rows)
    summary += f"\n## Detailed Data:\n"
    summary += (
        df[
            [
                "product_name",
                "subcategory_name",
                "units_sold",
                "total_revenue",
                "order_count",
            ]
        ]
        .head(50)
        .to_string(index=False)
    )

    return summary


def call_gemini_product_ai(data_summary: str, max_retries: int = 3) -> dict:
    """
    Call Gemini AI with the product sales data to get business advice.

    Args:
        data_summary: Formatted data summary
        max_retries: Maximum number of retry attempts

    Returns:
        dict: AI response or error
    """
    try:
        if genai is None:
            logger.warning(
                "Gemini client unavailable; skipping AI advice generation: %s",
                str(_GENAI_IMPORT_ERROR),
            )
            return {"error": "Gemini client not installed"}

        # Configure Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            return {"error": "API key not configured"}

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Construct prompt
        prompt = f"""Du er en erfaren dansk forretningsekspert med speciale i e-handel, produktoptimering og lagerstyring.

            Jeg giver dig produktomsætningsdata fra en e-handelsvirksomhed. Kolonnerne inkluderer:
            
            - product_name: Produktnavn
            - subcategory_name: Produkt underkategori
            - units_sold: Antal solgte enheder
            - total_revenue: Total omsætning i DKK
            - order_count: Antal ordre indeholdende produktet

            Data:
            {data_summary}

            Din opgave:
            1. Analyser produktsalgsdataen grundigt
            2. Identificer topsælgende produkter og deres bidrag til omsætningen
            3. Find produkter med lav omsætning (slow movers)
            4. Giv konkrete, handlingsorienterede forretningsråd på dansk inden for:
               - Prisoptimering: Hvilke produkter kan have for høj/lav pris?
               - Bundle-muligheder: Hvilke produkter kan med fordel sælges sammen?
               - Slow mover håndtering: Hvad skal vi gøre med produkter der sælger dårligt?
               - Lagerstyring: Hvornår skal vi genopfylde, og hvornår skal vi nedskrive?
            5. Undgå at kommentere på datakvalitet eller mangler

            Svar i struktureret markdown format med konkrete anbefalinger.
    
            Vigtige retningslinjer:
            - Svar kun på dansk
            - Vær kortfattet og præcis
            - Fokuser på konkrete handlinger virksomheden kan tage
            - Brug simple, forståelige termer (ikke teknisk jargon)
            - Brug markdown formatting hvor relevant
        """

        # Call API with retries
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                advice = response.text.strip()

                logger.info(
                    f"Successfully received AI product advice ({len(advice)} characters)"
                )
                return {"advice": advice}

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    import time

                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    raise

        return {"error": "Max retries exceeded"}

    except Exception as e:
        logger.error(f"Error calling Gemini AI: {str(e)}")
        return {"error": f"AI service error: {str(e)}"}


def save_ai_response(conn, user_id: str, response_text: str):
    """
    Save the AI response to the database.

    Args:
        conn: Database connection
        user_id: UUID of the user
        response_text: AI response text to save
    """
    try:
        cursor = conn.cursor()

        # Delete existing responses for this category and user
        delete_sql = """
        DELETE FROM ai_responses
        WHERE ai_category_id = %s AND user_id = %s
        """

        cursor.execute(delete_sql, ("product_business_advice", user_id))

        logger.info(
            f"Deleted {cursor.rowcount} existing AI response(s) for user {user_id}"
        )

        # Insert new response
        insert_sql = """
        INSERT INTO ai_responses (
            ai_category_id, response_text, user_id, created
        ) VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            insert_sql,
            (
                "product_business_advice",  # Category identifier
                response_text,
                user_id,
                datetime.now(),
            ),
        )

        conn.commit()
        logger.info(f"Successfully saved AI response for user {user_id}")

    except Exception as e:
        logger.error(f"Failed to save AI response: {str(e)}")
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            cursor.close()
        except Exception:
            pass


if __name__ == "__main__":
    # Example usage
    from dotenv import load_dotenv

    load_dotenv("./.env")

    db_usr = os.getenv("DB_USR_ADMIN")
    db_pwd = os.getenv("DB_PWD_ADMIN")

    result = get_product_advice(db_usr, db_pwd)
    print(json.dumps(result, indent=2, ensure_ascii=False))
