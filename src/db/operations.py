import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
import json
from src.db.models import CodegenChallenge, RegressionChallenge, CodegenResponse, RegressionResponse, ValidatorVersion, Score, Agent
from src.utils.cache import cached, cache_manager, invalidate_cache_pattern
from typing import List, Dict
import threading
import atexit
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
                    cls._instance._initialize_pool()
        return cls._instance

    def _initialize_pool(self):
        """Initialize the connection pool."""
        try:
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                host=os.getenv('AWS_RDS_PLATFORM_ENDPOINT'),
                user=os.getenv('AWS_MASTER_USERNAME'),
                password=os.getenv('AWS_MASTER_PASSWORD'),
                database=os.getenv('AWS_RDS_PLATFORM_DB_NAME'),
                sslmode='require'
            )
            # Register cleanup function
            atexit.register(self.close_all_connections)
        except Exception as e:
            print(f"Error initializing connection pool: {str(e)}")
            raise

    def get_connection(self):
        """Get a connection from the pool."""
        if self._pool is None:
            raise Exception("Connection pool not initialized")
        return self._pool.getconn()

    def return_connection(self, conn):
        """Return a connection to the pool."""
        if self._pool is None:
            return
        self._pool.putconn(conn)

    def close_all_connections(self):
        """Close all connections in the pool."""
        if self._pool:
            self._pool.closeall()
            self._pool = None

    def close(self):
        """Deprecated method for backward compatibility."""
        pass

    def store_codegen_challenge(self, challenge: CodegenChallenge) -> int:
        """Store a codegen challenge in the database (AWS Postgres RDS).
        This stores the challenge in both the challenges and codegen_challenges tables.
        Returns 1 on success, 0 on failure.
        """
        conn = None
        try:
            conn = self.get_connection()
            conn.autocommit = True
            with conn.cursor() as cursor:
                    # Insert into challenges table
                    cursor.execute("""
                        INSERT INTO challenges (challenge_id, type, validator_hotkey, created_at)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        challenge.challenge_id,
                        'codegen',
                        challenge.validator_hotkey,
                        challenge.created_at
                    ))

                    # Insert into codegen_challenges table
                    cursor.execute("""
                        INSERT INTO codegen_challenges (
                            challenge_id, problem_statement, dynamic_checklist,
                            repository_url, commit_hash, context_file_paths
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        challenge.challenge_id,
                        challenge.problem_statement,
                        json.dumps(challenge.dynamic_checklist),
                        challenge.repository_url,
                        challenge.commit_hash,
                        json.dumps(challenge.context_file_paths)
                    ))
            
            # Invalidate related caches when new data is added
            invalidate_cache_pattern("challenges")
            
            return 1
        except Exception as e:
            print(f"Error storing codegen challenge {getattr(challenge, 'challenge_id', None)}: {str(e)}")
            return 0
        finally:
            if conn:
                self.return_connection(conn)

    def store_regression_challenge(self, challenge: RegressionChallenge) -> int:
        """Store a regression challenge in the database (AWS Postgres RDS).
        This stores the challenge in both the challenges and regression_challenges tables.
        Returns 1 on success, 0 on failure.
        """
        conn = None
        try:
            conn = self.get_connection()
            conn.autocommit = True
            with conn.cursor() as cursor:
                    # Insert into challenges table
                    cursor.execute("""
                        INSERT INTO challenges (challenge_id, type, validator_hotkey, created_at)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        challenge.challenge_id,
                        'regression',
                        challenge.validator_hotkey,
                        challenge.created_at
                    ))

                    # Insert into regression_challenges table
                    cursor.execute("""
                        INSERT INTO regression_challenges (
                            challenge_id, problem_statement, repository_url,
                            commit_hash, context_file_paths
                        )
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        challenge.challenge_id,
                        challenge.problem_statement,
                        challenge.repository_url,
                        challenge.commit_hash,
                        json.dumps(challenge.context_file_paths)
                    ))
            
            # Invalidate related caches when new data is added  
            invalidate_cache_pattern("challenges")
            invalidate_cache_pattern("challenge_")
            
            return 1
        except Exception as e:
            print(f"Error storing regression challenge {getattr(challenge, 'challenge_id', None)}: {str(e)}")
            return 0
        finally:
            if conn:
                self.return_connection(conn)

    def store_codegen_response(self, response: CodegenResponse) -> int:
        """Store a codegen response in the database (AWS Postgres RDS).
        This stores the response in both the responses and codegen_responses tables.
        On conflict, only updates evaluation-related fields (evaluated, score, evaluated_at).
        Returns 1 on success, 0 on failure.
        """
        conn = None
        try:
            conn = self.get_connection()
            conn.autocommit = True
            with conn.cursor() as cursor:
                    # Insert or update into responses table
                    cursor.execute("""
                        INSERT INTO responses (
                            challenge_id, miner_hotkey, node_id, processing_time,
                            received_at, completed_at, evaluated, score, evaluated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (challenge_id, miner_hotkey) DO UPDATE SET
                            evaluated = EXCLUDED.evaluated,
                            score = EXCLUDED.score,
                            evaluated_at = EXCLUDED.evaluated_at
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

                    # Insert into codegen_responses table, ignore on conflict
                    cursor.execute("""
                        INSERT INTO codegen_responses (challenge_id, miner_hotkey, response_patch)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (challenge_id, miner_hotkey) DO NOTHING
                    """, (
                        response.challenge_id,
                        response.miner_hotkey,
                        response.response_patch
                    ))
            
            # Invalidate caches when responses are updated
            invalidate_cache_pattern("challenge_responses")
            invalidate_cache_pattern("miner_responses")
            
            return 1
        except Exception as e:
            print(f"Error storing codegen response for challenge {getattr(response, 'challenge_id', None)} from miner {getattr(response, 'miner_hotkey', None)}: {str(e)}")
            return 0
        finally:
            if conn:
                self.return_connection(conn)

    def store_regression_response(self, response: RegressionResponse) -> int:
        """Store a regression response in the database (AWS Postgres RDS).
        This stores the response in both the responses and regression_responses tables.
        Returns 1 on success, 0 on failure.
        """
        conn = None
        try:
            conn = self.get_connection()
            conn.autocommit = True
            with conn.cursor() as cursor:
                    # Insert into responses table
                    cursor.execute("""
                        INSERT INTO responses (
                            challenge_id, miner_hotkey, node_id, processing_time,
                            received_at, completed_at, evaluated, score, evaluated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (challenge_id, miner_hotkey) DO UPDATE SET
                            evaluated = EXCLUDED.evaluated,
                            score = EXCLUDED.score,
                            evaluated_at = EXCLUDED.evaluated_at
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

                    # Insert into regression_responses table, ignore on conflict
                    cursor.execute("""
                        INSERT INTO regression_responses (challenge_id, miner_hotkey, response_patch)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (challenge_id, miner_hotkey) DO NOTHING
                    """, (
                        response.challenge_id,
                        response.miner_hotkey,
                        response.response_patch
                    ))
            
            # Invalidate caches when responses are updated
            invalidate_cache_pattern("challenge_responses")
            invalidate_cache_pattern("miner_responses")
            
            return 1
        except Exception as e:
            print(f"Error storing regression response for challenge {getattr(response, 'challenge_id', None)} from miner {getattr(response, 'miner_hotkey', None)}: {str(e)}")
            return 0
        finally:
            if conn:
                self.return_connection(conn)

    def store_validator_version(self, validator_version: ValidatorVersion) -> int:
        """Store a validator version in the database (AWS Postgres RDS).
        Returns 1 on success, 0 on failure.
        """
        conn = None
        try:
            conn = self.get_connection()
            conn.autocommit = True
            with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO validator_versions (validator_hotkey, version, timestamp)
                        VALUES (%s, %s, %s)
                    """, (
                        validator_version.validator_hotkey,
                        validator_version.version,
                        validator_version.timestamp
                    ))
            return 1
        except Exception as e:
            print(f"Error storing validator version {getattr(validator_version, 'version', None)} for validator {getattr(validator_version, 'validator_hotkey', None)}: {str(e)}")
            return 0
        finally:
            if conn:
                self.return_connection(conn)

    def store_scores(self, scores: List[Score]) -> None:
        """Store multiple scores in the database (AWS Postgres RDS).
        Uses a single INSERT statement with multiple VALUES for optimal performance.
        """
        conn = None
        try:
            conn = self.get_connection()
            conn.autocommit = True
            with conn.cursor() as cursor:
                    values_template = "(%s, %s, %s, %s, %s)"
                    values_list = [
                        (score.type, score.validator_hotkey, score.miner_hotkey, score.score, score.challenge_id)
                        for score in scores
                    ]
                    flat_values = [val for tup in values_list for val in tup]
                    query = f"""
                        INSERT INTO scores (type, validator_hotkey, miner_hotkey, score, challenge_id)
                        VALUES {','.join([values_template] * len(scores))}
                    """
                    cursor.execute(query, flat_values)
        except Exception as e:
            print(f"Error storing scores: {str(e)}")
        finally:
            if conn:
                self.return_connection(conn)

    @cached("challenges")
    def get_codegen_challenges(self, challenge_id: str = None) -> List[Dict]:
        """Retrieve codegen challenges from the database (AWS Postgres RDS), including response_count for each challenge.
        Returns a list of dicts matching the original output format.
        response_count only includes responses where evaluated is TRUE and score is not NULL.
        """
        logger.debug(f"Fetching codegen challenges from database (challenge_id={challenge_id})")
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
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
                                cc.context_file_paths,
                                COUNT(r.challenge_id) AS response_count
                            FROM challenges c
                            INNER JOIN codegen_challenges cc ON c.challenge_id = cc.challenge_id
                            LEFT JOIN responses r ON c.challenge_id = r.challenge_id AND r.evaluated = TRUE AND r.score IS NOT NULL
                            WHERE c.challenge_id = %s AND c.type = 'codegen'
                            GROUP BY
                                c.challenge_id, c.type, c.validator_hotkey, c.created_at,
                                cc.problem_statement, cc.dynamic_checklist, cc.repository_url,
                                cc.commit_hash, cc.context_file_paths
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
                                cc.context_file_paths,
                                COUNT(r.challenge_id) AS response_count
                            FROM challenges c
                            INNER JOIN codegen_challenges cc ON c.challenge_id = cc.challenge_id
                            LEFT JOIN responses r ON c.challenge_id = r.challenge_id AND r.evaluated = TRUE AND r.score IS NOT NULL
                            WHERE c.type = 'codegen'
                            GROUP BY
                                c.challenge_id, c.type, c.validator_hotkey, c.created_at,
                                cc.problem_statement, cc.dynamic_checklist, cc.repository_url,
                                cc.commit_hash, cc.context_file_paths
                        """)
                    rows = cursor.fetchall()
                    if not rows:
                        return []
                    results = []
                    for row in rows:
                        result = {
                            'challenge_id': row[0],
                            'type': row[1],
                            'validator_hotkey': row[2],
                            'created_at': row[3],
                            'problem_statement': row[4],
                            'dynamic_checklist': json.loads(row[5]) if row[5] else None,
                            'repository_url': row[6],
                            'commit_hash': row[7],
                            'context_file_paths': json.loads(row[8]) if row[8] else None,
                            'response_count': row[9]
                        }
                        results.append(result)
                    return results
        except Exception as e:
            print(f"Error getting codegen challenges: {str(e)}")
            return []
        finally:
            if conn:
                self.return_connection(conn)
        
    @cached("challenge_responses")
    def get_codegen_challenge_responses(self, challenge_id: str) -> List[CodegenResponse]:
        """Retrieve a codegen challenge response from the database (AWS Postgres RDS).
        Returns a list of dictionaries containing the response.
        Only returns responses that have been evaluated (evaluated=true) and have a non-null score.
        """
        logger.debug(f"Fetching challenge responses from database (challenge_id={challenge_id})")
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
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
                        WHERE r.challenge_id = %s
                            AND r.evaluated = TRUE
                            AND r.score IS NOT NULL
                        ORDER BY r.completed_at DESC
                    """, (challenge_id,))
                    rows = cursor.fetchall()
                    
                    responses = []
                    for row in rows:
                        response_dict = {
                            'challenge_id': challenge_id,
                            'miner_hotkey': row[0],
                            'node_id': row[1],
                            'processing_time': row[2],
                            'received_at': row[3],
                            'completed_at': row[4],
                            'evaluated': row[5],
                            'score': row[6],
                            'evaluated_at': row[7],
                            'response_patch': row[8]
                        }
                        responses.append(CodegenResponse(**response_dict))
                    return responses
        except Exception as e:
            print(f"Error getting codegen challenge response: {str(e)}")
            return []
        finally:
            if conn:
                self.return_connection(conn)

    @cached("miner_responses")
    def get_miner_responses(self, challenge_id: str = None, miner_hotkey: str = None, min_score: float = 0, min_response_count: int = 0, sort_by_score: bool = False, max_miners: int = 5, hours: int = 24) -> List[Dict]:
        """Retrieve codegen responses from the database (AWS Postgres RDS).
        Returns a list of dictionaries containing miner information and their responses.
        Only includes responses where evaluated is TRUE and score is not NULL.
        
        Additional parameters:
        - min_score: Minimum average score for miners to be included
        - min_response_count: Minimum number of responses required per miner
        - sort_by_score: Whether to sort miners by average score
        - max_miners: Maximum number of miners to return
        - hours: Number of hours to look back (-1 for all time)
        """
        logger.debug(f"Fetching miner responses from database (challenge_id={challenge_id}, miner_hotkey={miner_hotkey}, params=min_score:{min_score},count:{min_response_count},sort:{sort_by_score},max:{max_miners},hours:{hours})")
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                    # Base query with optimized structure
                    base_query = """
                        WITH RECURSIVE time_bucket AS (
                            SELECT 
                                r.miner_hotkey,
                                r.challenge_id,
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
                            WHERE r.evaluated = TRUE 
                                AND r.score IS NOT NULL
                    """

                    # Add time filter if hours is not -1
                    if hours != -1:
                        base_query += " AND r.completed_at >= NOW() - INTERVAL '%s hours'"
                        params = [hours]
                    else:
                        params = []

                    # Add challenge_id or miner_hotkey filter if provided
                    if challenge_id:
                        base_query += " AND r.challenge_id = %s"
                        params.append(challenge_id)
                    elif miner_hotkey:
                        base_query += " AND r.miner_hotkey = %s"
                        params.append(miner_hotkey)

                    base_query += """
                        ),
                        miner_stats AS (
                            SELECT 
                                miner_hotkey,
                                COUNT(*) as response_count,
                                AVG(score) as average_score
                            FROM time_bucket
                            GROUP BY miner_hotkey
                            HAVING COUNT(*) >= %s AND AVG(score) >= %s
                        ),
                        miner_responses AS (
                            SELECT 
                                t.miner_hotkey,
                                json_agg(
                                    json_build_object(
                                        'challenge_id', t.challenge_id,
                                        'miner_hotkey', t.miner_hotkey,
                                        'node_id', t.node_id,
                                        'processing_time', t.processing_time,
                                        'received_at', t.received_at,
                                        'completed_at', t.completed_at,
                                        'evaluated', t.evaluated,
                                        'score', t.score,
                                        'evaluated_at', t.evaluated_at,
                                        'response_patch', t.response_patch
                                    )
                                    ORDER BY t.completed_at DESC
                                ) as responses
                            FROM time_bucket t
                            JOIN miner_stats ms ON t.miner_hotkey = ms.miner_hotkey
                            GROUP BY t.miner_hotkey
                        )
                        SELECT 
                            mr.miner_hotkey,
                            ms.response_count,
                            ms.average_score,
                            mr.responses
                        FROM miner_responses mr
                        JOIN miner_stats ms ON mr.miner_hotkey = ms.miner_hotkey
                    """

                    # Add final sorting
                    if sort_by_score:
                        base_query += " ORDER BY ms.average_score DESC, mr.miner_hotkey"
                    else:
                        base_query += " ORDER BY mr.miner_hotkey"

                    # Add final limit
                    base_query += " LIMIT %s"
                    params.extend([min_response_count, min_score, max_miners])

                    cursor.execute(base_query, params)
                    rows = cursor.fetchall()
                    if not rows:
                        return []
                    
                    return [
                        {
                            "miner_hotkey": row[0],
                            "response_count": row[1],
                            "average_score": row[2],
                            "responses": [CodegenResponse(**response) for response in row[3]]
                        }
                        for row in rows
                    ]
        except Exception as e:
            print(f"Error getting codegen challenge responses: {str(e)}")
            return []
        finally:
            if conn:
                self.return_connection(conn)

