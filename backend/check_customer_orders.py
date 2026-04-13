from src.scripts.db.populateDB import connectDB
import pymysql
import os

conn, _ = connectDB(os.getenv('DB_USR'), os.getenv('DB_PWD'))
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) as order_count, customer_id, billing_city FROM orders GROUP BY customer_id, billing_city ORDER BY order_count DESC LIMIT 10')
results = cursor.fetchall()
for row in results:
    print(f'{row[0]} orders from {row[2]} (customer {row[1]})')