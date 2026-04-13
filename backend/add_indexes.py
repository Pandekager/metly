from src.scripts.db.populateDB import connectDB
import os

conn, _ = connectDB(os.getenv('DB_USR_ADMIN'), os.getenv('DB_PWD_ADMIN'))

if conn:
    cursor = conn.cursor()
    
    # Add indexes for better query performance
    indexes = [
        ("idx_customers_user_id", "customers", "user_id"),
        ("idx_customers_billing_city", "customers", "billing_city"),
        ("idx_orders_customer_id", "orders", "customer_id"),
    ]
    
    for idx_name, table, column in indexes:
        try:
            cursor.execute(f"CREATE INDEX {idx_name} ON {table} ({column})")
            print(f"Created index {idx_name}")
        except Exception as e:
            print(f"Index {idx_name} may already exist: {e}")
    
    conn.commit()
    conn.close()
    print("Done adding indexes!")
else:
    print("Failed to connect to database")
