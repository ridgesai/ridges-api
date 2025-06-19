import os
import httpx
import uuid
from datetime import datetime

from src.utils.logging import get_logger
from src.db.operations import DatabaseManager
from src.utils.models import AgentVersionForValidator, EvaluationRun, Evaluation

logger = get_logger(__name__)

db = DatabaseManager()

def get_recent_commit_hashes(history_length: int = 30) -> list:
    """
    Get the previous commits from ridgesai/ridges.
    
    Returns:
        List of commit hashes (empty list if error)
    """
    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        # Add GitHub token if available for higher rate limits
        if token := os.getenv("GITHUB_TOKEN"):
            headers["Authorization"] = f"token {token}"
        
        with httpx.Client(timeout=10.0) as client:
            # Get last 30 commits
            response = client.get(f"https://api.github.com/repos/ridgesai/ridges/commits?per_page={history_length}", headers=headers)
            response.raise_for_status()
            commits = response.json()
            
            return [commit["sha"] for commit in commits]
            
    except Exception as e:
        logger.error(f"Failed to get commits: {e}")
        return []

def get_agent_to_evaluate(validator_hotkey: str) -> AgentVersionForValidator:
    """
    Gets the latest agent in queue to evaluate for a validator. 
    The agent it returns is the oldest agent unevaluated by the validator.

    Args:
        validator_hotkey (str): The hotkey of the validator requesting an agent to evaluate

    Returns:
        AgentVersion: The next agent version to be evaluated by this validator, or None if no agents are in queue
    """

    agent = db.get_latest_unevaluated_agent_version(validator_hotkey)

    if agent is None: 
        raise Exception("No agent found to evaluate")
    
    return agent
    
def update_validator_versions(response_json: dict, validator_versions: dict) -> dict:
    recent_commit_hashes = get_recent_commit_hashes()
    relative_version = recent_commit_hashes.index(response_json["version_commit_hash"]) if response_json["version_commit_hash"] in recent_commit_hashes else -1
    
    validator_versions[response_json["validator_hotkey"]] = {
        "relative_version": relative_version,
        "version_commit_hash": response_json["version_commit_hash"]
    }

    return validator_versions

def upsert_evaluation_run(evaluation_run: dict):
    evaluation_run = EvaluationRun(
        run_id=evaluation_run["run_id"],
        evaluation_id=evaluation_run["evaluation_id"],
        version_id=evaluation_run["version_id"],
        swebench_instance_id=evaluation_run["swebench_instance_id"],
        response=evaluation_run["response"],
        pass_to_fail_success=evaluation_run["pass_to_fail_success"],
        fail_to_pass_success=evaluation_run["fail_to_pass_success"],
        pass_to_pass_success=evaluation_run["pass_to_pass_success"],
        fail_to_fail_success=evaluation_run["fail_to_fail_success"],
        solved=evaluation_run["solved"],
        started_at=evaluation_run["started_at"],
        finished_at=evaluation_run["finished_at"]
    )
    db.store_evaluation_run(evaluation_run)

def create_evaluation(version_id: str, validator_hotkey: str) -> str:
    evaluation_object = Evaluation(
        evaluation_id=str(uuid.uuid4()),
        version_id=version_id,
        validator_hotkey=validator_hotkey,
        status="waiting",
        created_at=datetime.now()
    )
    db.store_evaluation(evaluation_object)
    return evaluation_object.evaluation_id
