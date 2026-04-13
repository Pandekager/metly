#!/usr/bin/env python3
"""
Script to migrate plaintext passwords to bcrypt hashed passwords.
This should be run once to secure existing user passwords in the database.
"""
from dotenv import load_dotenv
import os
import pymysql
from passlib.context import CryptContext

# Initialize password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Load environment variables
load_dotenv("./.env")
db_usr = os.getenv("DB_USR_ADMIN")
db_pwd = os.getenv("DB_PWD_ADMIN")


def migrate_passwords():
    """
    Migrate all plaintext passwords to bcrypt hashes.
    This assumes existing passwords are plaintext and need to be hashed.
    """
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
        print("Connected to database successfully.")

        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # Fetch all users with their current passwords
            cursor.execute("SELECT id, username, password FROM metlydk_main.users")
            users = cursor.fetchall()

            print(f"Found {len(users)} users to migrate.")

            for user in users:
                user_id = user["id"]
                username = user["username"]
                current_password = user["password"]

                # Check if password is already hashed (bcrypt hashes start with $2b$)
                if current_password and current_password.startswith("$2b$"):
                    print(f"  {username}: Already hashed, skipping.")
                    continue

                # Skip empty or None passwords
                if not current_password:
                    print(f"  {username}: No password set, skipping.")
                    continue

                # Hash the plaintext password
                try:
                    hashed_password = pwd_context.hash(current_password)
                except Exception as e:
                    print(f"  {username}: Failed to hash password: {e}")
                    continue

                # Update the password in the database
                update_query = """
                    UPDATE metlydk_main.users 
                    SET password = %s 
                    WHERE id = %s
                """
                cursor.execute(update_query, (hashed_password, user_id))
                print(f"  {username}: Password hashed and updated.")

            conn.commit()
            print("\nPassword migration completed successfully!")

        conn.close()

    except Exception as e:
        print(f"Migration failed: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Password Migration Script")
    print("=" * 60)
    print("This script will hash all plaintext passwords in the database.")
    print("WARNING: This is a one-way operation.")
    print("=" * 60)

    response = input("\nDo you want to proceed? (yes/no): ")
    if response.lower() in ["yes", "y"]:
        migrate_passwords()
    else:
        print("Migration cancelled.")
