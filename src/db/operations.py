import json
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import timedelta
from pathlib import Path
import logging

from src.db.models import CodegenChallenge, CodegenResponse
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
        """Store a codegen challenge in the database.
        
        This stores the challenge in both the challenges and codegen_challenges tables.
        """
        conn = self.get_connection()
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

    def store_codegen_response(self, response: CodegenResponse) -> None:
        """Store a codegen response in the database.
        
        This stores the response in both the responses and codegen_responses tables.
        """
        conn = self.get_connection()
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
