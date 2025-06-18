import os
import httpx

from src.db.operations import DatabaseManager
from src.utils.logging import get_logger
from src.utils.models import AgentVersion

logger = get_logger(__name__)


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

def get_agent_to_evaluate(validator_hotkey: str, db: DatabaseManager) -> AgentVersion:
    """
    Gets the latest agent in queue to evaluate for a validator. 
    The agent it returns is the oldest agent unevaluated by the validator.

    Args:
        validator_hotkey (str): The hotkey of the validator requesting an agent to evaluate

    Returns:
        AgentVersion: The next agent version to be evaluated by this validator, or None if no agents are in queue
    """

    agent = db.get_latest_unevaluated_agent(validator_hotkey)

    if agent is None: 
        raise Exception("No agent found to evaluate")
    
    return agent
    
def update_validator_versions(response_json: dict, validator_versions: dict) -> dict:
    recent_commit_hashes = get_recent_commit_hashes(response_json["version_commit_hash"])
    relative_version = recent_commit_hashes.index(response_json["version_commit_hash"]) if response_json["version_commit_hash"] in recent_commit_hashes else -1
    
    validator_versions[response_json["validator_hotkey"]] = {
        "relative_version": relative_version,
        "version_commit_hash": response_json["version_commit_hash"]
    }

    return validator_versions