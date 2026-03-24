from src.scripts.db.populateDB import connectDB
import pymysql
import os

conn, _ = connectDB(os.getenv('DB_USR'), os.getenv('DB_PWD'))
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) as order_count, customer_id FROM orders GROUP BY customer_id ORDER BY order_count DESC LIMIT 10')
results = cursor.fetchall()
for row in results:
    print(f'{row[0]} orders from customer {row[1]}')