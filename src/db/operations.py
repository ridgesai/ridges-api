from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from db.schema import Agent, CodegenChallenge, Challenge, Base
from typing import List

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

    def get_agent(self, agent_id: str) -> Agent:
        with Session(self.engine) as session:
            return session.query(Agent).filter(Agent.agent_id == agent_id).first()
        
    def get_agents(self, type: str = None) -> List[Agent]:
        with Session(self.engine) as session:
            if type:
                return session.query(Agent).filter(Agent.type == type).all()
            else:
                return session.query(Agent).all()

