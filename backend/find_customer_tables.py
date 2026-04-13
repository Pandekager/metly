from src.scripts.db.populateDB import connectDB
import pymysql
import os

conn, _ = connectDB(os.getenv('DB_USR'), os.getenv('DB_PWD'))
cursor = conn.cursor()
cursor.execute("SHOW TABLES LIKE '%customer%'")
tables = cursor.fetchall()
for table in tables:
    print(table[0])