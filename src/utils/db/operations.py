import json
import sqlite3
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import logging

from src.models.codegen_challenges import CodegenChallenge
from src.models.codegen_response import CodegenResponse
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
                VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)
            """, (
                challenge.challenge_id,
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
                INSERT INTO responses (
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
                    problem_statement=row["problem_statement"],
                    dynamic_checklist=json.loads(row["dynamic_checklist"]),
                    repository_name=row["repository_name"],
                    commit_hash=row["commit_hash"],
                    context_file_paths=json.loads(row["context_file_paths"]),
                    prompt="",
                    model="",
                )
            return None
        
    def cleanup_old_data(self, days: int = 7) -> None:
        """
        Remove data older than the specified number of days from various tables.

        Args:
            days: Number of days to keep data for. Default is 7.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Define tables and their timestamp columns
            tables_to_clean = [
                ("responses", "received_at"),
                ("challenge_assignments", "completed_at"),
            ]

            for table, timestamp_column in tables_to_clean:
                query = f"""
                DELETE FROM {table}
                WHERE {timestamp_column} < datetime('now', '-{days} days')
                """
                cursor.execute(query)
                deleted_rows = cursor.rowcount
                logger.info(f"Deleted {deleted_rows} rows from {table} older than {days} days")

            # Clean up challenges that are no longer referenced
            cursor.execute("""
                DELETE FROM challenges
                WHERE challenge_id NOT IN (
                    SELECT DISTINCT challenge_id FROM responses
                    UNION
                    SELECT DISTINCT challenge_id FROM challenge_assignments
                )
                AND created_at < datetime('now', '-{days} days')
            """)
            deleted_challenges = cursor.rowcount
            logger.info(f"Deleted {deleted_challenges} orphaned challenges older than {days} days")

            conn.commit()
            logger.info(f"Database cleanup completed for data older than {days} days")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error during database cleanup: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def get_global_miner_scores(self, hours: int = 24) -> Tuple[float, int]:
        """Gets the average score for all miners and average number of responses for each miner over the last n hours"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT 
                    AVG(score) as global_avg_score,
                    COUNT(*) / COUNT(DISTINCT miner_hotkey) as avg_responses_per_miner
                FROM responses 
                WHERE evaluated = TRUE 
                AND evaluated_at > datetime('now',  '-' || ? || ' hours')
            """, (hours,))

            global_average, average_count = cursor.fetchone()

            return global_average, average_count

        finally:
            cursor.close()
            conn.close()
        
    def get_bayesian_miner_score(
        self,
        global_average: float,
        average_count: int,
        hours: int = 24
    ): 
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT 
                    miner_hotkey,
                    COUNT(*) as response_count,
                    AVG(score) as avg_score,
                    (COUNT(*) * AVG(score) + ? * ?) / (COUNT(*) + ?) as bayesian_avg
                FROM responses
                WHERE evaluated = TRUE 
                AND evaluated_at > datetime('now', '-' || ? || ' hours')
                GROUP BY miner_hotkey       
            """, (average_count, global_average, average_count, hours,))

            results = cursor.fetchall()

            return results
        finally:
            cursor.close()
            conn.close()

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
