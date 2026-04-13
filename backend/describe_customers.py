from src.scripts.db.populateDB import connectDB
import pymysql
import os

conn, _ = connectDB(os.getenv('DB_USR'), os.getenv('DB_PWD'))
cursor = conn.cursor()
cursor.execute('DESCRIBE customers')
columns = cursor.fetchall()
for col in columns:
    print(f"{col[0]}: {col[1]}")

print("\n\nSample data:")
cursor.execute('SELECT * FROM customers LIMIT 3')
rows = cursor.fetchall()
for row in rows:
    print(row)