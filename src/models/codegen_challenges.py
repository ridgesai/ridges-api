from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from textwrap import dedent
from datetime import datetime

class CodegenChallenge(BaseModel):
    challenge_id: str
    created_at: datetime
    problem_statement: str
    dynamic_checklist: List[str]
    repository_name: str
    commit_hash: Optional[str]
    context_file_paths: List[str]
