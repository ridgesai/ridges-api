from pydantic import BaseModel
from typing import List

from src.db.models import CodegenChallenge

class ReturnedResponse(BaseModel):
    miner_hotkey: str
    response_patch: str
    score: float
    completion_time_seconds: float
    
class CodegenChallengeResponses(BaseModel):
    challenge: CodegenChallenge
    responses: List[ReturnedResponse]
