import json
import sqlite3
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import logging

from src.models.codegen_challenges import CodegenChallenge
from src.models.codegen_response import CodegenResponse
from src.models.miner_responses import MinerResponses
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

    def store_codegen_challenge(self, challenge: CodegenChallenge) -> None:
        """Store a new challenge in the database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR IGNORE INTO codegen_challenges (
                    challenge_id, created_at, problem_statement, dynamic_checklist,
                    repository_name, commit_hash, context_file_paths
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                challenge.challenge_id,
                challenge.created_at,
                challenge.problem_statement,
                json.dumps(challenge.dynamic_checklist),
                challenge.repository_name,
                challenge.commit_hash,
                json.dumps(challenge.context_file_paths)
            ))

            if cursor.rowcount == 0:
                logger.debug(f"Challenge {challenge.challenge_id} already exists in database")
            else:
                logger.info(f"Stored new challenge {challenge.challenge_id} in database")

            conn.commit()
        except Exception as e:
            logger.error(f"Error storing {challenge.challenge_id} in database: {e}")
        finally:
            conn.close()
    
    def store_response(self, response: CodegenResponse) -> int:
        """Store a miner's response to a challenge"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:

            # Store response
            cursor.execute("""
                INSERT OR REPLACE INTO responses (
                    challenge_id,
                    miner_hotkey,
                    node_id,
                    response_patch,
                    received_at,
                    completed_at,
                    evaluated,
                    score,
                    evaluated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                response.challenge_id,
                response.miner_hotkey,
                response.node_id,
                response.response_patch,
                response.received_at,
                response.completed_at,
                response.evaluated,
                response.score,
                response.evaluated_at
            ))

            response_id = cursor.lastrowid

            conn.commit()
            return response_id

        finally:
            conn.close()
    
    def get_challenge(self, challenge_id: str) -> Optional[CodegenChallenge]:
        """Get a challenge from the database by ID"""
        conn = self.get_connection()
        with conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            logger.info(f"Challenge ID: {challenge_id}")
            # log type of challenge_id
            logger.info(f"Type of challenge_id: {type(challenge_id)}")
            cursor.execute("""
                SELECT *
                FROM codegen_challenges 
                WHERE challenge_id = ?
            """, (challenge_id,))
            row = cursor.fetchone()

            if row:
                return CodegenChallenge(
                    challenge_id=row["challenge_id"],
                    created_at=row["created_at"],
                    problem_statement=row["problem_statement"],
                    dynamic_checklist=json.loads(row["dynamic_checklist"]),
                    repository_name=row["repository_name"],
                    commit_hash=row["commit_hash"],
                    context_file_paths=json.loads(row["context_file_paths"]),
                )
            return None
        
    def get_responses(self, challenge_id: str, max_rows: int) -> List[CodegenResponse]:
        "Get a list of responses for a given challenge"
        conn = self.get_connection()
        with conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT *
                FROM responses
                WHERE challenge_id = ?
                AND evaluated = 1
                LIMIT ?
            """, (challenge_id, max_rows))
            rows = cursor.fetchall()

            if rows:
                return [CodegenResponse(**dict(row)) for row in rows]
            else:
                return []
            
    def get_miner_responses(self, miner_hotkey: str, max_rows: int = 100) -> List[CodegenResponse]:
        conn = self.get_connection()
        with conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT *
                FROM responses
                WHERE miner_hotkey = ?
                AND evaluated = 1
                LIMIT ?
            """, (miner_hotkey, max_rows))
            rows = cursor.fetchall()

            if rows:
                return [CodegenResponse(**dict(row)) for row in rows]
            else:
                return []

    def get_all_table_entries(
        self, 
        table_name: str,
        since: Optional[timedelta] = timedelta(days=1)
    ) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()

        TABLE_TO_DATETIME_MAP = {
            "codegen_challenges": "created_at",
            "responses": "received_at",
        }

        try:
            if not since:
                cursor.execute(f"SELECT * FROM {table_name}")
                return [dict(row) for row in cursor.fetchall()]
            
            # If since exists, see if its a supported table
            time_field_name = TABLE_TO_DATETIME_MAP.get(table_name)

            if time_field_name is None:
                raise NotImplementedError(f"Provided table {table_name} does not have a table time field recorded. Please add this tables time field name to fetch all rows since a date.")

            cursor.execute(f"SELECT * FROM {table_name} WHERE datetime({time_field_name}) > datetime('now', '-{since.total_seconds()} seconds')")
            return [dict(row) for row in cursor.fetchall()]
        
        except Exception as e:
            logger.error(f"Error getting table data: {str(e)}")

        finally:
            cursor.close()
            conn.close()
