import os
import psycopg2
from dotenv import load_dotenv
import json
from src.utils.models import Agent
from typing import List, Dict

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('AWS_RDS_PLATFORM_ENDPOINT'),
            user=os.getenv('AWS_MASTER_USERNAME'),
            password=os.getenv('AWS_MASTER_PASSWORD'),
            database=os.getenv('AWS_RDS_PLATFORM_DB_NAME'),
            sslmode='require'
        )
        self.conn.autocommit = True

    def close(self):
        if self.conn:
            self.conn.close()

    def get_connection(self):
        return psycopg2.connect(
            host=os.getenv('AWS_RDS_PLATFORM_ENDPOINT'),
            user=os.getenv('AWS_MASTER_USERNAME'),
            password=os.getenv('AWS_MASTER_PASSWORD'),
            database=os.getenv('AWS_RDS_PLATFORM_DB_NAME'),
            sslmode='require'
        ) 
        
    def store_agent(self, agent: Agent) -> int:
        """Store an agent in the database (AWS Postgres RDS).
        Returns 1 on success, 0 on failure.
        """
        try:
            conn = self.get_connection()
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO agents (agent_id, miner_hotkey, created_at, last_updated, latest_version)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (agent_id) DO UPDATE SET
                            last_updated = EXCLUDED.last_updated,
                            latest_version = EXCLUDED.latest_version
                    """, (
                        agent.agent_id,
                        agent.miner_hotkey,
                        agent.created_at,
                        agent.last_updated,
                        agent.latest_version
                    ))
                conn.commit()
            return 1
        except Exception as e:
            print(f"Error storing agent {getattr(agent, 'agent_id', None)}: {str(e)}")
            return 0
        
    def get_agents(self, type: str = None) -> List[Agent]:
        """Retrieve all agents from the database (AWS Postgres RDS).
        Returns a list of Agent objects.
        """
        conn = self.get_connection()
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM agents
                    """)
                    if type:
                        cursor.execute("""
                            SELECT * FROM agents WHERE type = %s
                        """, (type,))
                    else:
                        cursor.execute("""
                            SELECT * FROM agents
                        """)
                    rows = cursor.fetchall()
                    return [
                        Agent(
                            agent_id=row[0],
                            miner_hotkey=row[1], 
                            created_at=row[2],
                            last_updated=row[3],
                            type=row[4],
                            version=row[5],
                            elo=row[6],
                            num_responses=row[7]
                        ) 
                        for row in rows]
        except Exception as e:
            print(f"Error getting agents: {str(e)}")
            return []
        
    def get_agent(self, agent_id: str) -> Agent:
        """Retrieve an agent from the database (AWS Postgres RDS).
        Returns an Agent object.
        """
        conn = self.get_connection()
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM agents WHERE agent_id = %s
                    """, (agent_id,))
                    row = cursor.fetchone()
                    if row:
                        return Agent(
                            agent_id=row[0],
                            miner_hotkey=row[1],
                            created_at=row[2],
                            last_updated=row[3],
                            type=row[4],
                            version=row[5],
                            elo=row[6],
                            num_responses=row[7]
                        )
                    return None
        except Exception as e:
            print(f"Error getting agent {agent_id}: {str(e)}")
            return None
