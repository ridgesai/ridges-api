from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from db.schema import Agent, CodegenChallenge, Challenge, Base
from src.utils.config import AGENT_FIELDS

class DatabaseManager:
    def __init__(self, db_path: Path):
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
    
    def add_codegen_challenge(self, codegen_challenge: CodegenChallenge):
        with Session(self.engine) as session:
            session.add(codegen_challenge)
            session.commit()
    
    def add_challenge(self, challenge: Challenge):
        with Session(self.engine) as session:
            session.add(challenge)
            session.commit()

    def add_agent(self, agent: Agent):
        with Session(self.engine) as session:
            session.merge(agent)
            session.commit()
        
    def get_agents(
            self, 
            agent_id: str = None,
            miner_hotkey: str = None,
            type: str = None,
            created_at_min: datetime = None,
            created_at_max: datetime = None,
            last_updated_min: datetime = None,
            last_updated_max: datetime = None,
            version_min: int = None,
            version_max: int = None,
            elo_min: int = None,
            elo_max: int = None,
            num_responses_min: int = None,
            num_responses_max: int = None,
            order_by: str = "elo",
            order_asc: bool = False,
            ) -> List[Agent]:
        if order_by not in AGENT_FIELDS:
            raise ValueError(f"Invalid order_by value: {order_by}. Must be one of {AGENT_FIELDS}")
            
        with Session(self.engine) as session:
            query = session.query(Agent)
            if agent_id:
                query = query.filter(Agent.agent_id == agent_id)
            if miner_hotkey:
                query = query.filter(Agent.miner_hotkey == miner_hotkey)
            if type:
                query = query.filter(Agent.type == type)
            if created_at_min:
                query = query.filter(Agent.created_at >= created_at_min)
            if created_at_max:
                query = query.filter(Agent.created_at <= created_at_max)
            if last_updated_min:
                query = query.filter(Agent.last_updated >= last_updated_min)
            if last_updated_max:
                query = query.filter(Agent.last_updated <= last_updated_max)
            if version_min:
                query = query.filter(Agent.version >= version_min)
            if version_max:
                query = query.filter(Agent.version <= version_max)
            if elo_min:
                query = query.filter(Agent.elo >= elo_min)
            if elo_max:
                query = query.filter(Agent.elo <= elo_max)
            if num_responses_min:
                query = query.filter(Agent.num_responses >= num_responses_min)
            if num_responses_max:
                query = query.filter(Agent.num_responses <= num_responses_max)

            query = query.order_by(getattr(Agent, order_by).desc() if not order_asc else getattr(Agent, order_by))

            return query.all()

