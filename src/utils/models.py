from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Agent(BaseModel):
    agent_id: str
    miner_hotkey: str
    latest_version: int
    created_at: datetime
    last_updated: datetime
