from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CodegenChallenge(BaseModel):
    challenge_id: str
    type: str
    validator_hotkey: str
    created_at: datetime
    problem_statement: str
    dynamic_checklist: str
    repository_url: str
    commit_hash: Optional[str]
    context_file_paths: str

class CodegenChallengeWithResponseCount(CodegenChallenge):
    response_count: int = 0

class RegressionChallenge(BaseModel):
    challenge_id: str
    type: str
    validator_hotkey: str
    created_at: datetime
    problem_statement: str
    dynamic_checklist: str
    repository_url: str
    commit_hash: Optional[str]
    context_file_paths: str

class CodegenResponse(BaseModel):
    challenge_id: str
    miner_hotkey: str
    node_id: Optional[int] = None
    processing_time: Optional[float] = None
    received_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    evaluated: Optional[bool] = False
    score: Optional[float] = None
    evaluated_at: Optional[datetime] = None
    response_patch: str

class CodegenChallengeWithResponseList(CodegenChallenge):
    response_list: List[CodegenResponse] = []

class RegressionResponse(BaseModel):
    challenge_id: str
    miner_hotkey: str
    node_id: Optional[int] = None
    processing_time: Optional[float] = None
    received_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    evaluated: Optional[bool] = False
    score: Optional[float] = None
    evaluated_at: Optional[datetime] = None
    response_patch: str

class Agent(BaseModel):
    agent_id: str
    miner_hotkey: str
    created_at: datetime
    last_updated: datetime
    type: str
    version: int
    elo: int
    num_responses: int
