from src.scripts.db.populateDB import connectDB
import pymysql
import os

conn, _ = connectDB(os.getenv('DB_USR'), os.getenv('DB_PWD'))
cursor = conn.cursor()
cursor.execute('DESCRIBE orders')
columns = cursor.fetchall()
for col in columns:
    print(f"{col[0]}: {col[1]}")