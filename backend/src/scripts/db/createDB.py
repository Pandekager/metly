from pathlib import Path
from dotenv import load_dotenv
import os
import pymysql
from src.scripts.db.populateDB import connectDB
import string
import secrets
import random
from passlib.context import CryptContext

# Initialize password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def authenticateDB(db_usr, db_pwd):
    if not db_usr or not db_pwd:
        print("Database credentials not found in environment variables.")
        return

    try:
        conn = pymysql.connect(
            host="metly.dk",
            port=3306,
            user=db_usr,
            password=db_pwd,
            database="metlydk_main",
        )
        print("Connection OK")
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")


def createTables(db_usr, db_pwd):

    if not db_usr or not db_pwd:
        print("Database credentials not found in environment variables.")
        return

    try:
        conn = pymysql.connect(
            host="metly.dk",
            port=3306,
            user=db_usr,
            password=db_pwd,
            database="metlydk_main",
        )

        sql_file_path = Path("./src/db/createTables.sql")
        if not sql_file_path.exists():
            print("SQL file 'createTables.sql' not found.")
            return

        with open(sql_file_path, "r") as f:
            sql_script = f.read()

        with conn.cursor() as cursor:
            for statement in sql_script.split(";"):
                stmt = statement.strip()
                if stmt and stmt != "":
                    cursor.execute(stmt)
            conn.commit()
        print("Tables created successfully.")

        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")


def gen_password(length: int = 14) -> str:
    if length < 3:
        raise ValueError("Password length must be at least 3")
    lowers = string.ascii_lowercase
    uppers = string.ascii_uppercase
    digits = string.digits
    all_chars = lowers + uppers + digits

    # ensure at least one lower, one upper and one digit
    pw = [
        secrets.choice(lowers),
        secrets.choice(uppers),
        secrets.choice(digits),
    ]
    for _ in range(length - 3):
        pw.append(secrets.choice(all_chars))

    random.SystemRandom().shuffle(pw)
    return "".join(pw)


def createUser(db_usr, db_pwd, platform: str, email: str, api_key: str, tenant: str):

    try:
        conn, df_users = connectDB(db_usr, db_pwd)
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    if not df_users[df_users["username"] == email].empty:
        print(f"User {email} already exists.")
        return

    try:
        # Generate a secure random password
        plaintext_password = gen_password(14)
        # Hash the password using bcrypt
        hashed_password = pwd_context.hash(plaintext_password)

        create_user_query = f"""
            INSERT INTO metlydk_main.users
            (id, username, password, created, platform_id, tenant, client_id, client_secret)
            VALUES(uuid(), '{email}', '{hashed_password}', current_timestamp(), '{platform}', '{tenant}', NULL, '{api_key}');
            """

        with conn.cursor() as cursor:
            cursor.execute(create_user_query)
            conn.commit()
        print(f"User created successfully.")
        print(f"  Email: {email}")
        print(f"  Temporary password: {plaintext_password}")
        print(f"  IMPORTANT: Save this password securely. It cannot be recovered.")

        conn.close()

    except Exception as e:
        print(f"Connection failed: {e}")


if __name__ == "__main__":
    # load .env
    load_dotenv("./.env")
    db_usr = os.getenv("DB_USR_ADMIN")
    db_pwd = os.getenv("DB_PWD_ADMIN")

    authenticateDB(db_usr, db_pwd)
    createTables(db_usr, db_pwd)

    # Enter new client for the system
    # createUser(db_usr, db_pwd, platform, email, api_key, tenant)
