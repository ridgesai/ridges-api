import boto3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

AWS_MASTER_USERNAME = os.getenv('AWS_MASTER_USERNAME')
AWS_MASTER_PASSWORD = os.getenv('AWS_MASTER_PASSWORD')
AWS_RDS_PLATFORM_ENDPOINT = os.getenv('AWS_RDS_PLATFORM_ENDPOINT')
AWS_RDS_PLATFORM_DB_NAME = os.getenv('AWS_RDS_PLATFORM_DB_NAME')

client = boto3.client("rds", region_name="us-east-1")

response = client.describe_db_instances()
db_instances = response['DBInstances']

for instance in db_instances:
    print(f"DB Instance: {instance['DBInstanceIdentifier']}")

    if instance['DBInstanceIdentifier'] == 'platform':
        db_response = client.describe_db_instances(DBInstanceIdentifier=instance['DBInstanceIdentifier'])
        print(f"Databases in platform instance: {db_response}")
        break

def create_database_if_not_exists(db_name):
    # Use environment variables for connection info
    conn = psycopg2.connect(
        host=AWS_RDS_PLATFORM_ENDPOINT,
        user=AWS_MASTER_USERNAME,
        password=AWS_MASTER_PASSWORD,
        database=AWS_RDS_PLATFORM_DB_NAME,
        sslmode='require'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    try:
        with conn.cursor() as cur:
            # Check if database exists
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            exists = cur.fetchone()
            
            if not exists:
                # Create the database
                cur.execute(f'CREATE DATABASE {db_name}')
                print(f"Database '{db_name}' created successfully")
            else:
                print(f"Database '{db_name}' already exists")
    finally:
        conn.close()

# Example usage
create_database_if_not_exists('platform_db')

