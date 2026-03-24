import os
from dotenv import load_dotenv
from scripts.db.populateDB import connectDB


def getTopPairs():
    # load .env
    load_dotenv("./.env")
    db_usr = os.getenv("DB_USR")
    db_pwd = os.getenv("DB_PWD")

    conn, df_users = connectDB(db_usr, db_pwd)
