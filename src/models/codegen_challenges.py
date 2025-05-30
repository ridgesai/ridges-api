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

    def to_detailed_format(self) -> str:
        context_files_string = ""
        for i, file in enumerate(self.context_file_paths):
            context_files_string += f"# File {i} used to solve the problem: {file}"
        return dedent(f"""
        Problem Statement: {self.problem_statement}
        Checklist of items to consider: {self.dynamic_checklist}
        {context_files_string}
        """)

    def to_dict(self) -> Dict[str, Any]:
        """Convert challenge to dictionary for sending to miners"""
        return {
            "challenge_id": self.challenge_id,
            "created_at": self.created_at.isoformat(),
            "problem_statement": self.problem_statement,
            "dynamic_checklist": self.dynamic_checklist,
            "repository_name": self.repository_name,
            "commit_hash": self.commit_hash,
            "context_file_paths": self.context_file_paths
        }