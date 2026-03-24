from src.scripts.db.populateDB import connectDB
import pymysql
import os

conn, _ = connectDB(os.getenv('DB_USR'), os.getenv('DB_PWD'))
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT billing_city FROM orders WHERE billing_city IS NOT NULL AND billing_city != '' LIMIT 10")
results = cursor.fetchall()
for row in results:
    print(row[0])