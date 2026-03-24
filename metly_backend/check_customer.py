from src.scripts.db.populateDB import connectDB
import pymysql
import os

conn, _ = connectDB(os.getenv('DB_USR'), os.getenv('DB_PWD'))
cursor = conn.cursor()
cursor.execute('SELECT * FROM customer LIMIT 1')
columns = [desc[0] for desc in cursor.description]
print('\n'.join(columns))