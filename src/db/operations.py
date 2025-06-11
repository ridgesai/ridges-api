import os
import psycopg2
from dotenv import load_dotenv
import json
from src.db.models import CodegenChallenge, RegressionChallenge, CodegenResponse, RegressionResponse, ValidatorVersion, Score, Agent
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

    def store_codegen_challenge(self, challenge: CodegenChallenge) -> int:
        """Store a codegen challenge in the database (AWS Postgres RDS).
        This stores the challenge in both the challenges and codegen_challenges tables.
        Returns 1 on success, 0 on failure.
        """
        try:
            conn = self.get_connection()
            with conn:
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
                conn.commit()
            return 1
        except Exception as e:
            print(f"Error storing codegen challenge {getattr(challenge, 'challenge_id', None)}: {str(e)}")
            return 0

    def store_regression_challenge(self, challenge: RegressionChallenge) -> int:
        """Store a regression challenge in the database (AWS Postgres RDS).
        This stores the challenge in both the challenges and regression_challenges tables.
        Returns 1 on success, 0 on failure.
        """
        try:
            conn = self.get_connection()
            with conn:
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
                conn.commit()
            return 1
        except Exception as e:
            print(f"Error storing regression challenge {getattr(challenge, 'challenge_id', None)}: {str(e)}")
            return 0

    def store_codegen_response(self, response: CodegenResponse) -> int:
        """Store a codegen response in the database (AWS Postgres RDS).
        This stores the response in both the responses and codegen_responses tables.
        On conflict, only updates evaluation-related fields (evaluated, score, evaluated_at).
        Returns 1 on success, 0 on failure.
        """
        try:
            conn = self.get_connection()
            with conn:
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
                conn.commit()
            return 1
        except Exception as e:
            print(f"Error storing codegen response for challenge {getattr(response, 'challenge_id', None)} from miner {getattr(response, 'miner_hotkey', None)}: {str(e)}")
            return 0

    def store_regression_response(self, response: RegressionResponse) -> int:
        """Store a regression response in the database (AWS Postgres RDS).
        This stores the response in both the responses and regression_responses tables.
        Returns 1 on success, 0 on failure.
        """
        try:
            conn = self.get_connection()
            with conn:
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
                conn.commit()
            return 1
        except Exception as e:
            print(f"Error storing regression response for challenge {getattr(response, 'challenge_id', None)} from miner {getattr(response, 'miner_hotkey', None)}: {str(e)}")
            return 0

    def store_validator_version(self, validator_version: ValidatorVersion) -> int:
        """Store a validator version in the database (AWS Postgres RDS).
        Returns 1 on success, 0 on failure.
        """
        try:
            conn = self.get_connection()
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO validator_versions (validator_hotkey, version, timestamp)
                        VALUES (%s, %s, %s)
                    """, (
                        validator_version.validator_hotkey,
                        validator_version.version,
                        validator_version.timestamp
                    ))
                conn.commit()
            return 1
        except Exception as e:
            print(f"Error storing validator version {getattr(validator_version, 'version', None)} for validator {getattr(validator_version, 'validator_hotkey', None)}: {str(e)}")
            return 0

    def store_score(self, score: Score) -> int:
        """Store a score in the database (AWS Postgres RDS).
        Returns 1 on success, 0 on failure.
        """
        try:
            conn = self.get_connection()
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO scores (type, validator_hotkey, miner_hotkey, score)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        score.type,
                        score.validator_hotkey,
                        score.miner_hotkey,
                        score.score,
                    ))
                conn.commit()
            return 1
        except Exception as e:
            print(f"Error storing score for validator {getattr(score, 'validator_hotkey', None)} and miner {getattr(score, 'miner_hotkey', None)}: {str(e)}")
            return 0

    def get_codegen_challenges(self, challenge_id: str = None) -> List[Dict]:
        """Retrieve codegen challenges from the database (AWS Postgres RDS), including response_count for each challenge.
        Returns a list of dicts matching the original output format.
        response_count only includes responses where evaluated is TRUE and score is not NULL.
        """
        conn = self.get_connection()
        try:
            with conn:
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
            conn.close()

    def get_codegen_challenge_responses(self, challenge_id: str = None) -> List[CodegenResponse]:
        """Retrieve codegen responses from the database (AWS Postgres RDS).
        Returns a list of CodegenResponse objects matching the original output format.
        Only includes responses where evaluated is TRUE and score is not NULL.
        """
        conn = self.get_connection()
        try:
            with conn:
                with conn.cursor() as cursor:
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
                            WHERE r.challenge_id = %s AND r.evaluated = TRUE AND r.score IS NOT NULL
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
                            WHERE r.evaluated = TRUE AND r.score IS NOT NULL
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
        finally:
            conn.close()

