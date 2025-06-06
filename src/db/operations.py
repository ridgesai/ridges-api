import json
import sqlite3
from pathlib import Path
import logging
from typing import List, Optional

from src.db.models import CodegenChallenge, RegressionChallenge, CodegenResponse, RegressionResponse, Agent, CodegenChallengeWithResponseCount
from .schema import check_db_initialized, init_db

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

        # Initialize database if needed
        if not check_db_initialized(str(db_path)):
            logger.info(f"Initializing new database at {db_path}")
            init_db(str(db_path))
        
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Connected to database at {db_path}")

    def close(self):
        if self.conn:
            self.conn.close()

    def get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)
    
    def store_codegen_challenge(self, challenge: CodegenChallenge) -> int:
        """Store a codegen challenge in the database.
        
        This stores the challenge in both the challenges and codegen_challenges tables.
        """
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                
                # First insert into challenges table
                cursor.execute("""
                    INSERT INTO challenges (challenge_id, type, validator_hotkey, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    challenge.challenge_id,
                    'codegen',
                    challenge.validator_hotkey,
                    challenge.created_at
                ))
                
                # Then insert into codegen_challenges table
                cursor.execute("""
                    INSERT INTO codegen_challenges (
                        challenge_id, problem_statement, dynamic_checklist,
                        repository_url, commit_hash, context_file_paths
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    challenge.challenge_id,
                    challenge.problem_statement,
                    json.dumps(challenge.dynamic_checklist),
                    challenge.repository_url,
                    challenge.commit_hash,
                    json.dumps(challenge.context_file_paths)
                ))
                conn.commit()
                logger.info(f"Stored codegen challenge {challenge.challenge_id}")
                return 1
        except Exception as e:
            logger.error(f"Error storing codegen challenge {challenge.challenge_id}: {str(e)}")
            return 0

    def store_regression_challenge(self, challenge: RegressionChallenge) -> int:
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                
                # First insert into challenges table
                cursor.execute("""
                    INSERT INTO challenges (challenge_id, type, validator_hotkey, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    challenge.challenge_id,
                    'regression',
                    challenge.validator_hotkey, 
                    challenge.created_at
                ))
                
                # Then insert into regression_challenges table
                cursor.execute("""
                    INSERT INTO regression_challenges (
                        challenge_id, problem_statement, repository_url,
                        commit_hash, context_file_paths
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    challenge.challenge_id,
                    challenge.problem_statement,
                    challenge.repository_url,
                    challenge.commit_hash,
                    json.dumps(challenge.context_file_paths)
                ))
                conn.commit()
                logger.info(f"Stored regression challenge {challenge.challenge_id}")
                return 1
        except Exception as e:
            logger.error(f"Error storing regression challenge {challenge.challenge_id}: {str(e)}")
            return 0

    def store_codegen_response(self, response: CodegenResponse) -> int:
        """Store a codegen response in the database.
        
        This stores the response in both the responses and codegen_responses tables.
        """
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                
                # First insert into responses table
                cursor.execute("""
                    INSERT INTO responses (
                        challenge_id, miner_hotkey, node_id, processing_time,
                        received_at, completed_at, evaluated, score, evaluated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    response.challenge_id,
                    response.miner_hotkey,
                    response.node_id,
                    response.processing_time,
                    response.received_at,
                    response.completed_at,
                    response.evaluated,
                    response.score,
                    response.evaluated_at
                ))
                
                # Then insert into codegen_responses table
                cursor.execute("""
                    INSERT INTO codegen_responses (challenge_id, miner_hotkey, response_patch)
                    VALUES (?, ?, ?)
                """, (
                    response.challenge_id,
                    response.miner_hotkey,
                    response.response_patch
                ))
                
                conn.commit()
                logger.info(f"Stored codegen response for challenge {response.challenge_id} from miner {response.miner_hotkey}")
                return 1
        except Exception as e:
            logger.error(f"Error storing codegen response for challenge {response.challenge_id} from miner {response.miner_hotkey}: {str(e)}")
            return 0
        
    def store_regression_response(self, response: RegressionResponse) -> int:
        """Store a regression response in the database.
        
        This stores the response in both the responses and regression_responses tables.
        """
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()

                # First insert into responses table
                cursor.execute("""
                    INSERT INTO responses (
                        challenge_id, miner_hotkey, node_id, processing_time,
                        received_at, completed_at, evaluated, score, evaluated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    response.challenge_id,
                    response.miner_hotkey,
                    response.node_id,
                    response.processing_time,
                    response.received_at,
                    response.completed_at,
                    response.evaluated,
                    response.score,
                    response.evaluated_at
                ))

                # Then insert into regression_responses table
                cursor.execute("""
                    INSERT INTO regression_responses (challenge_id, miner_hotkey, response_patch)
                    VALUES (?, ?, ?)
                """, (
                    response.challenge_id,
                    response.miner_hotkey,
                    response.response_patch
                ))

                conn.commit()
                logger.info(f"Stored regression response for challenge {response.challenge_id} from miner {response.miner_hotkey}")
                return 1
        except Exception as e:
            logger.error(f"Error storing regression response for challenge {response.challenge_id} from miner {response.miner_hotkey}: {str(e)}")
            return 0

    def store_agent(self, agent: Agent) -> int:
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                
                # First insert into agents table
                cursor.execute("""
                    INSERT INTO agents (agent_id, miner_hotkey, created_at, last_updated, type, version, elo, num_responses)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    agent.agent_id,
                    agent.miner_hotkey,
                    agent.created_at,
                    agent.last_updated,
                    agent.type,
                    agent.version,
                    agent.elo,
                    agent.num_responses
                ))
                conn.commit()
                logger.info(f"Stored agent {agent.agent_id}")
                return 1
        except Exception as e:
            logger.error(f"Error storing agent {agent.agent_id}: {str(e)}")
            return 0
        
    def get_codegen_challenges(self, challenge_id: Optional[str] = None, max_challenges: int = 5) -> List[CodegenChallenge]:
        conn = self.get_connection()
        
        with conn:
            cursor = conn.cursor()

            if challenge_id:
                cursor.execute("""
                    SELECT 
                        c.challenge_id,
                        c.type,
                        c.validator_hotkey,
                        c.created_at,
                        cc.problem_statement,
                        cc.dynamic_checklist,
                        cc.repository_url,
                        cc.commit_hash,
                        cc.context_file_paths
                    FROM challenges c
                    INNER JOIN codegen_challenges cc ON c.challenge_id = cc.challenge_id
                    WHERE c.challenge_id = ? AND c.type = 'codegen'
                """, (challenge_id,))
            else:
                cursor.execute("""
                    SELECT 
                        c.challenge_id,
                        c.type,
                        c.validator_hotkey,
                        c.created_at,
                        cc.problem_statement,
                        cc.dynamic_checklist,
                        cc.repository_url,
                        cc.commit_hash,
                        cc.context_file_paths
                    FROM challenges c
                    INNER JOIN codegen_challenges cc ON c.challenge_id = cc.challenge_id
                    WHERE c.type = 'codegen'
                    LIMIT ?
                """, (max_challenges,))
            
            rows = cursor.fetchall()
            if not rows:
                return []
            
            # Convert rows to dictionaries and parse JSON fields
            results = []
            for row in rows:
                result = {
                    'challenge_id': row[0],
                    'type': row[1],
                    'validator_hotkey': row[2],
                    'created_at': row[3],
                    'problem_statement': row[4],
                    'dynamic_checklist': json.loads(row[5]),
                    'repository_url': row[6],
                    'commit_hash': row[7],
                    'context_file_paths': json.loads(row[8]),
                    'response_count': 0
                }
                results.append(result)
            
            return results
        
    def get_codegen_challenge_responses(self, challenge_id: str = None) -> List[CodegenResponse]:
        conn = self.get_connection()
        with conn:
            cursor = conn.cursor()
            if challenge_id:
                cursor.execute("""
                    SELECT 
                        r.challenge_id,
                        r.miner_hotkey,
                        r.node_id,
                        r.processing_time,
                        r.received_at,
                        r.completed_at,
                        r.evaluated,
                        r.score,
                        r.evaluated_at,
                        cr.response_patch
                    FROM responses r
                    JOIN codegen_responses cr 
                        ON r.challenge_id = cr.challenge_id 
                        AND r.miner_hotkey = cr.miner_hotkey
                    WHERE r.challenge_id = ?
                """, (challenge_id,))
            else:
                cursor.execute("""
                    SELECT 
                        r.challenge_id,
                        r.miner_hotkey,
                        r.node_id,
                        r.processing_time,
                        r.received_at,
                        r.completed_at,
                        r.evaluated,
                        r.score,
                        r.evaluated_at,
                        cr.response_patch
                    FROM responses r
                    JOIN codegen_responses cr 
                        ON r.challenge_id = cr.challenge_id 
                        AND r.miner_hotkey = cr.miner_hotkey
                """)
            rows = cursor.fetchall()
            if not rows:
                return []
            
            return [
                CodegenResponse(
                    challenge_id=row[0],
                    miner_hotkey=row[1],
                    node_id=row[2],
                    processing_time=row[3],
                    received_at=row[4],
                    completed_at=row[5],
                    evaluated=row[6],
                    score=row[7],
                    evaluated_at=row[8],
                    response_patch=row[9]
                )
                for row in rows
            ]
