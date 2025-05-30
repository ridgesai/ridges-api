from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class CodegenResponse(BaseModel):
    """Expected response format for codegen challenges"""
    challenge_id: str
    node_id: Optional[int] = None
    miner_hotkey: Optional[str] = None
    response_id: Optional[int] = None
    received_at: Optional[datetime] = None
    score: Optional[float] = None
    evaluated: bool = False
    evaluated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    response_patch: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "challenge_id": self.challenge_id,
            "node_id": self.node_id,
            "miner_hotkey": self.miner_hotkey,
            "response_id": self.response_id,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "score": self.score,
            "evaluated": self.evaluated,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
            "response_patch": self.response_patch
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodegenResponse':
        received_at = data.get('received_at')
        if received_at and isinstance(received_at, str):
            received_at = datetime.fromisoformat(received_at)
        evaluated_at = data.get('evaluated_at')
        if evaluated_at and isinstance(evaluated_at, str):
            evaluated_at = datetime.fromisoformat(evaluated_at)
        return cls(
            challenge_id=data['challenge_id'],
            processing_time=data.get('processing_time'),
            node_id=data.get('node_id'),
            miner_hotkey=data.get('miner_hotkey'),
            response_id=data.get('response_id'),
            received_at=received_at,
            score=data.get('score'),
            evaluated=data.get('evaluated', False),
            evaluated_at=evaluated_at,
            response_patch=data.get('response_patch')
        )