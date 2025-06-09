import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def print_all_tables():
    conn = psycopg2.connect(
        host=os.getenv('AWS_RDS_PLATFORM_ENDPOINT'),
        user=os.getenv('AWS_MASTER_USERNAME'),
        password=os.getenv('AWS_MASTER_PASSWORD'),
        database=os.getenv('AWS_RDS_PLATFORM_DB_NAME'),
        sslmode='require'
    )
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cur.fetchall()
            print("Tables in the database:")
            for table in tables:
                print(table[0])
    finally:
        conn.close()

# Usage
print_all_tables()

