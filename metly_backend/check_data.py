from src.scripts.db.populateDB import connectDB
import os
import pymysql

conn, _ = connectDB(os.getenv('DB_USR'), os.getenv('DB_PWD'))
cursor = conn.cursor()

# Get first user
cursor.execute("SELECT id FROM users LIMIT 1")
user_id = cursor.fetchone()[0]
print(f"User: {user_id}")

# Check customers with billing_city
cursor.execute("""
    SELECT billing_city, COUNT(*) as cnt 
    FROM customers 
    WHERE user_id = %s AND billing_city IS NOT NULL AND billing_city != ''
    GROUP BY billing_city
""", (str(user_id),))
cities = cursor.fetchall()
print(f"\nCustomers with cities: {len(cities)}")
for c in cities[:5]:
    print(f"  {c[0]}: {c[1]} customers")

# Check orders linked to customers
cursor.execute("""
    SELECT COUNT(*) 
    FROM orders o
    JOIN customers c ON o.customer_id = c.id
    WHERE c.user_id = %s
""", (str(user_id),))
orders_linked = cursor.fetchone()[0]
print(f"\nOrders linked to customers: {orders_linked}")

# Check all orders for user
cursor.execute("SELECT COUNT(*) FROM orders WHERE customer_id IS NOT NULL")
total = cursor.fetchone()[0]
print(f"Total orders with customer_id: {total}")