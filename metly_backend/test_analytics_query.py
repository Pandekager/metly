from src.scripts.db.populateDB import connectDB
import pymysql
import os
import json

conn, _ = connectDB(os.getenv('DB_USR'), os.getenv('DB_PWD'))
cursor = conn.cursor()

# Get a user_id from the users table
cursor.execute("SELECT id FROM users LIMIT 1")
user_id = cursor.fetchone()[0]

print(f"Testing with user_id: {user_id}")

# Run the analytics query for that user
sql = """
    SELECT 
        c.billing_city AS city,
        COUNT(o.id) AS order_count,
        COALESCE(SUM(o.total), 0) AS revenue
    FROM customers c
    LEFT JOIN orders o ON c.id = o.customer_id
    WHERE c.user_id = %s
        AND c.billing_city IS NOT NULL 
        AND c.billing_city != ''
    GROUP BY c.billing_city
    ORDER BY revenue DESC
"""
cursor.execute(sql, (str(user_id),))
rows = cursor.fetchall()

print(f"\nFound {len(rows)} cities with data:")
for row in rows:
    city, order_count, revenue = row
    print(f"  {city}: {order_count} orders, {revenue} revenue")

# Also check if customers table has billing_city data for this user
cursor.execute("SELECT billing_city, COUNT(*) FROM customers WHERE user_id = %s AND billing_city IS NOT NULL AND billing_city != '' GROUP BY billing_city", (str(user_id),))
cities = cursor.fetchall()
print(f"\nCustomers with cities: {len(cities)} unique cities")