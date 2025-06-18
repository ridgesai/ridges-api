from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Agent(BaseModel):
    agent_id: str
    miner_hotkey: str
    latest_version: int
    created_at: datetime
    last_updated: datetime

class AgentVersion(BaseModel):
    version_id: str
    agent_id: str
    version_num: int
    created_at: datetime
    score: Optional[float]
