"""
Generate demo customer data for analytics.

Creates 50 customers per user distributed across 10 Danish cities.
"""
from dotenv import load_dotenv
import os
import pymysql
import random
from datetime import datetime, timedelta
from src.scripts.db.populateDB import connectDB
import uuid

# 10 largest Danish cities with approximate coordinates
DANISH_CITIES = [
    ("Copenhagen", 55.6761, 12.5683),
    ("Aarhus", 56.1629, 10.2039),
    ("Odense", 55.4030, 10.3834),
    ("Aalborg", 57.0476, 9.9256),
    ("Esbjerg", 55.4898, 8.4516),
    ("Randers", 56.4599, 10.0379),
    ("Kolding", 55.4918, 9.4690),
    ("Horsens", 55.8629, 9.8509),
    ("Viborg", 56.4500, 9.4000),
    ("Silkeborg", 56.1693, 9.7958)
]

FIRST_NAMES = [
    "Jens", "Maria", "Peter", "Lene", "Anders", "Søren", "Mette", "Kristian",
    "Camilla", "Morten", "Henrik", "Pia", "Martin", "Anne", "Lars", "Karin",
    "Thomas", "Line", "Jesper", "Marianne"
]

LAST_NAMES = [
    "Jensen", "Nielsen", "Hansen", "Pedersen", "Andersen", "Christensen",
    "Larsen", "Rasmussen", "Sørensen", "Jørgensen", "Petersen", "Madsen",
    "Kristensen", " Olsen", "Thomsen", "Christiansen", "Møller", "Boye"
]

STREET_NAMES = [
    "Østergade", "Vestergade", "Nørregade", "Søndergade", "Frederiksberg Allé",
    "Amager Boulevard", "H.C. Andersens Vej", "Nørrebrogade", "Vesterbrogade",
    "Øresundsvej"
]

def generate_customer_data(user_id, num_customers=50):
    """Generate customer data for a specific user."""
    customers = []
    # Distribute customers across cities (roughly equal distribution with some randomness)
    cities_with_counts = []
    base_count = num_customers // len(DANISH_CITIES)
    remainder = num_customers % len(DANISH_CITIES)
    
    for i, (city, lat, lng) in enumerate(DANSH_CITIES):
        count = base_count + (1 if i < remainder else 0)
        # Add some randomness to distribution
        count = max(1, count + random.randint(-2, 2))
        cities_with_counts.append((city, lat, lng, count))
    
    # Adjust total to match target
    total = sum(count for _, _, _, count in cities_with_counts)
    if total != num_customers:
        # Adjust first city
        city, lat, lng, count = cities_with_counts[0]
        cities_with_counts[0] = (city, lat, lng, count + (num_customers - total))
    
    customer_id_counter = 0
    for city, lat, lng, count in cities_with_counts:
        for _ in range(count):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            street_num = random.randint(1, 200)
            street = random.choice(STREET_NAMES)
            address = f"{street_num} {street}"
            zip_codes = ["1000", "2000", "8000", "9000", "7100", "8660", "4684", "6700", "7800", "8900"]
            zip_code = random.choice(zip_codes)
            email = f"{first_name.lower()}.{last_name.lower()}@example.dk"
            
            customer_id = f"demo_{uuid.uuid4().hex[:10]}"
            customers.append({
                "id": customer_id,
                "user_id": str(user_id),
                "billing_firstName": first_name,
                "billing_lastName": last_name,
                "billing_addressLine": address,
                "billing_city": city,
                "billing_zipCode": zip_code,
                "billing_email": email,
                "extended_internal": None,
                "extended_external": None,
                "created": datetime.now() - timedelta(days=random.randint(1, 365))
            })
            customer_id_counter += 1
    
    return customers

def populate_demo_customers(db_usr, db_pwd):
    """Main function to populate demo customers for all users."""
    conn, df_users = connectDB(db_usr, db_pwd)
    if conn is None or df_users is None:
        print("Failed to connect to database")
        return
    
    try:
        cursor = conn.cursor()
        
        # Get distinct users
        cursor.execute("SELECT DISTINCT id FROM users")
        user_ids = [row[0] for row in cursor.fetchall()]
        print(f"Found {len(user_ids)} users")
        
        total_customers_created = 0
        
        for user_id in user_ids:
            print(f"Processing user: {user_id}")
            
            # Check how many customers this user already has
            cursor.execute(
                "SELECT COUNT(*) FROM customers WHERE user_id = %s",
                (str(user_id),)
            )
            existing_count = cursor.fetchone()[0]
            
            # Only add demo customers if user has less than 30
            # (to avoid overwhelming real data)
            if existing_count >= 30:
                print(f"  User already has {existing_count} customers, skipping...")
                continue
            
            # Generate demo customers
            customers_to_add = max(0, 50 - existing_count)
            if customers_to_add < 10:
                # If already has some, just add enough to reach 20 for demo
                customers_to_add = max(0, 20 - existing_count)
            
            if customers_to_add == 0:
                print(f"  User already has sufficient customers")
                continue
            
            new_customers = generate_customer_data(user_id, customers_to_add)
            
            # Insert customers
            insert_sql = """
                INSERT INTO customers 
                (id, user_id, billing_firstName, billing_lastName, billing_addressLine,
                 billing_city, billing_zipCode, billing_email, extended_internal,
                 extended_external, created)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for customer in new_customers:
                cursor.execute(insert_sql, (
                    customer["id"],
                    customer["user_id"],
                    customer["billing_firstName"],
                    customer["billing_lastName"],
                    customer["billing_addressLine"],
                    customer["billing_city"],
                    customer["billing_zipCode"],
                    customer["billing_email"],
                    customer["extended_internal"],
                    customer["extended_external"],
                    customer["created"]
                ))
            
            conn.commit()
            total_customers_created += len(new_customers)
            print(f"  Added {len(new_customers)} customers for user {user_id}")
        
        print(f"\nTotal customers created: {total_customers_created}")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    load_dotenv("./.env")
    db_usr = os.getenv("DB_USR_ADMIN")
    db_pwd = os.getenv("DB_PWD_ADMIN")
    
    if not db_usr or not db_pwd:
        print("Database credentials not found in environment variables")
        exit(1)
    
    populate_demo_customers(db_usr, db_pwd)