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


def get_business_advice(db_usr, db_pwd, user_ids=None):
    """
    Fetch forecast data for a user, send to Gemini AI for business advice,
    and save the response to the database.

    Args:
        db_usr: Database username
        db_pwd: Database password

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
            df_users = df_users[df_users["id"].astype(str).isin(allowed_user_ids)].copy()

        for _, user in df_users.iterrows():

            # Query forecast data
            query = """
            SELECT subcategory_name, date, ROUND(amount, 0) AS amount, is_forecast, user_id
            FROM forecasts
            WHERE 1=1
                AND date >= '2025-11-01'
                AND ROUND(amount, 0) != 0
                AND user_id = %s
            ORDER BY subcategory_name, date
            """

            cursor = conn.cursor()
            cursor.execute(query, (user["id"],))
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(results, columns=columns)

            if df.empty:
                logger.warning(f"No forecast data found for user {user['id']}")
                continue

            logger.info(f"Retrieved {len(df)} forecast records for user {user['id']}")

            # Prepare data summary for AI
            data_summary = prepare_data_summary(df)

            # Call Gemini AI
            ai_response = call_gemini_ai(data_summary)

            if "error" in ai_response:
                return ai_response

            # Save AI response to database
            response_text = ai_response.get("advice", "")
            save_ai_response(conn, user["id"], response_text)

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error in get_business_advice: {str(e)}")
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


def prepare_data_summary(df: pd.DataFrame) -> str:
    """
    Prepare a concise summary of the forecast data for the AI.

    Args:
        df: DataFrame with forecast data

    Returns:
        str: Formatted data summary
    """
    # Convert date to string for better formatting
    df = df[["subcategory_name", "date", "amount", "is_forecast"]].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    # Separate historical and forecast data
    df_historical = df[df["is_forecast"] == 0]
    df_forecast = df[df["is_forecast"] == 1]

    summary = "# Sales Data Analysis\n\n"

    # Category overview
    categories = df["subcategory_name"].unique()
    summary += f"## Product Categories ({len(categories)} total):\n"
    for cat in categories:
        cat_data = df[df["subcategory_name"] == cat]
        total_hist = cat_data[cat_data["is_forecast"] == 0]["amount"].sum()
        total_forecast = cat_data[cat_data["is_forecast"] == 1]["amount"].sum()
        summary += f"- {cat}: Historical sales: {int(total_hist)}, Forecasted sales: {int(total_forecast)}\n"

    summary += "\n## Detailed Data:\n"
    summary += df.to_string(index=False, max_rows=100)

    summary += f"\n\n## Summary Statistics:\n"
    summary += f"- Total historical records: {len(df_historical)}\n"
    summary += f"- Total forecast records: {len(df_forecast)}\n"
    summary += f"- Date range: {df['date'].min()} to {df['date'].max()}\n"

    return summary


def call_gemini_ai(data_summary: str, max_retries: int = 3) -> dict:
    """
    Call Gemini AI with the forecast data to get business advice.

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
        prompt = f"""Du er en erfaren dansk forretningsekspert med speciale i e-handel og data analyse.

            Jeg giver dig salgsdata fra en e-handelsvirksomhed, som indeholder både historiske salgstal og fremskrivninger.
            Kolonnerne inkluderer følgende:
            
            - subcategory_name
                - Produkt underkategori
            - date
                - Dato for salget, eller fremskrivningsdato
            - amount
                - Salgsantal
            - is_forecast
                - Indikator for om data er en fremskrivning (1) eller historisk (0)

            Data:
            {data_summary}

            Din opgave:
            1. Analyser salgsdataen grundigt
            2. Identificer trends, mønstre og anomalier
            3. Giv konkrete, handlingsorienterede forretningsråd på dansk
            4. Fokuser på strategier for at optimere salg og vækst baseret på dataen
            5. Undgå at kommentere på datakvalitet eller mangler

            Svar i struktureret markdown format:
                "Din korte, præcise forretningsrådgivning her (maks 300 ord)"
    

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
                    f"Successfully received AI advice ({len(advice)} characters)"
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

        cursor.execute(delete_sql, ("forecast_business_advice", user_id))

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
                "forecast_business_advice",  # Category identifier
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

    result = get_business_advice(db_usr, db_pwd)
    print(json.dumps(result, indent=2, ensure_ascii=False))
