import os
import psycopg2
from dotenv import load_dotenv
from src.utils.models import Agent, AgentVersion
from logging import getLogger

load_dotenv()

logger = getLogger(__name__)

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
        
    def get_agent(self, miner_hotkey: str) -> Agent:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM agents WHERE miner_hotkey = %s
            """, (miner_hotkey,))
            row = cursor.fetchone()
            if row:
                return Agent(
                    agent_id=row[0],
                    miner_hotkey=row[1],
                    latest_version=row[2],
                    created_at=row[3],
                    last_updated=row[4]
                )
            return None
        
    def store_agent(self, agent: Agent) -> int:
        """
        Store an agent in the database. If the agent already exists, update latest_version and last_updated. Return 1 if successful, 0 if not.
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO agents (agent_id, miner_hotkey, latest_version, created_at, last_updated)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (agent_id) DO UPDATE SET
                        latest_version = EXCLUDED.latest_version,
                        last_updated = EXCLUDED.last_updated
                """, (agent.agent_id, agent.miner_hotkey, agent.latest_version, agent.created_at, agent.last_updated))
                logger.info(f"Agent {agent.agent_id} stored successfully")
                return 1
        except Exception as e:
            logger.error(f"Error storing agent {agent.agent_id}: {str(e)}")
            return 0
        
    def store_agent_version(self, agent_version: AgentVersion) -> int:
        """
        Store an agent version in the database. Return 1 if successful, 0 if not. If the agent version already exists, update the score.
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO agent_versions (version_id, agent_id, version_num, created_at, score)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (version_id) DO UPDATE SET
                        score = EXCLUDED.score
                    """, (agent_version.version_id, agent_version.agent_id, agent_version.version_num, agent_version.created_at, agent_version.score))
                logger.info(f"Agent version {agent_version.version_id} stored successfully")
                return 1
        except Exception as e:
            logger.error(f"Error storing agent version {agent_version.version_id}: {str(e)}")
            return 0
