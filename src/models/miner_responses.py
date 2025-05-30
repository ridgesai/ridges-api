from pydantic import BaseModel
from typing import List

class ReturnedCodegenChallenge(BaseModel):
    challenge_id: str
    problem_statement: str
    dynamic_checklist: List[str]
    repository_name: str
    context_file_paths: List[str]

class ReturnedCodegenResponses(BaseModel):
    codegen_challenge: ReturnedCodegenChallenge
    completion_time_seconds: float
    patch: str
    score: float

class MinerResponses(BaseModel):
    miner_hotkey: str
    responses: List[ReturnedCodegenResponses]
