import os
import psycopg2
from dotenv import load_dotenv
from src.utils.models import Agent, AgentVersion, EvaluationRun, AgentVersionForValidator, Evaluation
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
        """
        Close the database connection.
        """
        if self.conn:
            self.conn.close()
        
    def get_agent(self, miner_hotkey: str) -> Agent:
        """
        Get an agent from the database. Return None if not found.
        """
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
        
    def get_agent_version(self, version_id: str) -> AgentVersion:
        """
        Get an agent version from the database. Return None if not found.
        """
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM agent_versions WHERE version_id = %s
            """, (version_id,))
            row = cursor.fetchone()
            if row:
                return AgentVersion(
                    version_id=row[0],
                    agent_id=row[1],
                    version_num=row[2],
                    created_at=row[3],
                    score=row[4]
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
    
    def store_evaluation(self, evaluation: Evaluation) -> int:
        """
        Store an evaluation in the database. Return 1 if successful, 0 if not. If the evaluation already exists, update the status, started_at, and finished_at.
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO evaluations (evaluation_id, version_id, validator_hotkey, status, created_at, started_at, finished_at, terminated_reason)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (evaluation_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        started_at = EXCLUDED.started_at,
                        finished_at = EXCLUDED.finished_at
                        terminated_reason = EXCLUDED.terminated_reason
                """, (evaluation.evaluation_id, evaluation.version_id, evaluation.validator_hotkey, evaluation.status, evaluation.created_at, evaluation.started_at, evaluation.finished_at, evaluation.terminated_reason))
                logger.info(f"Evaluation {evaluation.evaluation_id} stored successfully")
                return 1
        except Exception as e:
            logger.error(f"Error storing evaluation {evaluation.evaluation_id}: {str(e)}")
            return 0

    def store_evaluation_run(self, evaluation_run: EvaluationRun) -> int:
        """
        Store an evaluation run in the database. Return 1 if successful, 0 if not.
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO evaluation_runs (run_id, version_id, validator_hotkey, swebench_instance_id, response, pass_to_fail_success, fail_to_pass_success, pass_to_pass_success, fail_to_fail_success, solved, started_at, finished_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (run_id) DO UPDATE SET
                        response = EXCLUDED.response,
                        pass_to_fail_success = EXCLUDED.pass_to_fail_success,
                        fail_to_pass_success = EXCLUDED.fail_to_pass_success,
                        pass_to_pass_success = EXCLUDED.pass_to_pass_success,
                        fail_to_fail_success = EXCLUDED.fail_to_fail_success,
                        solved = EXCLUDED.solved,
                        finished_at = EXCLUDED.finished_at
                """, (evaluation_run.run_id, evaluation_run.version_id, evaluation_run.validator_hotkey, evaluation_run.swebench_instance_id, evaluation_run.response, evaluation_run.pass_to_fail_success, evaluation_run.fail_to_pass_success, evaluation_run.pass_to_pass_success, evaluation_run.fail_to_fail_success, evaluation_run.solved, evaluation_run.started_at, evaluation_run.finished_at))
                logger.info(f"Evaluation run {evaluation_run.run_id} stored successfully")
                return 1
        except Exception as e:
            logger.error(f"Error storing evaluation run {evaluation_run.run_id}: {str(e)}")
            return 0
    
    def get_latest_unevaluated_agent_version(self, validator_hotkey: str) -> AgentVersionForValidator:
        """
        Get the latest unevaluated agent version for a validator. Return None if not found.
        """
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT av.*, a.miner_hotkey
                FROM agent_versions av
                JOIN agents a ON av.agent_id = a.agent_id
                WHERE av.version_num = (
                    SELECT MAX(av2.version_num)
                    FROM agent_versions av2
                    WHERE av2.agent_id = av.agent_id
                )
                AND NOT EXISTS (
                    SELECT 1 
                    FROM evaluation_runs er 
                    WHERE er.validator_hotkey = %s
                    AND er.version_id = av.version_id
                )
                ORDER BY av.created_at ASC
                LIMIT 1;
            """, (validator_hotkey,))
            row = cursor.fetchone()
            if row:
                logger.info(f"Latest unevaluated agent version found for validator {validator_hotkey}")
                return AgentVersionForValidator(
                    version_id=row[0],
                    agent_id=row[1], 
                    version_num=row[2],
                    created_at=row[3],
                    score=row[4],
                    miner_hotkey=row[5]
                )
            else:
                logger.info(f"No unevaluated agent version found for validator {validator_hotkey}")
            return None
