from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, validator, field_validator
from src.utils.config import AGENT_TYPES

# Base models for shared attributes
class ChallengeBase(BaseModel):
    challenge_id: str
    created_at: datetime
    type: str
    validator_hotkey: str

    model_config = ConfigDict(from_attributes=True)

class CodegenChallengeBase(BaseModel):
    challenge_id: str
    validator_hotkey: str
    created_at: datetime
    problem_statement: str
    dynamic_checklist: str
    repository_url: str
    commit_hash: Optional[str] = None
    context_file_paths: str

    model_config = ConfigDict(from_attributes=True)

class AgentBase(BaseModel):
    agent_id: str
    miner_hotkey: str
    created_at: datetime
    last_updated: datetime
    type: str
    version: int
    elo: int
    num_responses: int

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in AGENT_TYPES:
            raise ValueError(f"Invalid agent type: {v}. Must be one of {AGENT_TYPES}")
        return v

    model_config = ConfigDict(from_attributes=True)

class ResponseBase(BaseModel):
    challenge_id: str
    agent_id: str
    miner_hotkey: str
    node_id: Optional[int] = None
    processing_time: Optional[float] = None
    received_at: datetime
    completed_at: Optional[datetime] = None
    evaluated: bool = False
    score: Optional[float] = None
    evaluated_at: Optional[datetime] = None
    response_patch: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# Create models (for input validation)
class ChallengeCreate(ChallengeBase):
    pass

class CodegenChallengeCreate(CodegenChallengeBase):
    pass

class AgentCreate(AgentBase):
    pass

class ResponseCreate(ResponseBase):
    pass

# Read models (for output serialization)
class ResponseRead(ResponseBase):
    challenge: Optional["ChallengeRead"] = None
    agent: Optional["AgentRead"] = None

class AgentRead(AgentBase):
    responses: List[ResponseRead] = []

class CodegenChallengeRead(CodegenChallengeBase):
    challenge: Optional["ChallengeRead"] = None

class ChallengeRead(ChallengeBase):
    codegen_challenges: Optional[CodegenChallengeRead] = None
    responses: List[ResponseRead] = []

# Update forward references
ChallengeRead.model_rebuild()
CodegenChallengeRead.model_rebuild()
ResponseRead.model_rebuild()
AgentRead.model_rebuild()
