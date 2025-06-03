from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from db.schema import Agent, CodegenChallenge, Challenge, Base

class DatabaseManager:
    def __init__(self, db_path: Path):
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.storage_dir = Path("agent_storage")
        self.storage_dir.mkdir(exist_ok=True)
        Base.metadata.create_all(self.engine)
    
    def store_agent_zip(self, agent_id: str, zip_data: bytes) -> str:
        """Store agent zip file and return the path"""
        file_path = self.storage_dir / f"{agent_id}.zip"
        with open(file_path, "wb") as f:
            f.write(zip_data)
        return str(file_path)
    
    def get_agent_zip(self, agent_id: str) -> bytes:
        """Retrieve agent zip file"""
        file_path = self.storage_dir / f"{agent_id}.zip"
        if not file_path.exists():
            raise FileNotFoundError(f"No zip file found for agent {agent_id}")
        with open(file_path, "rb") as f:
            return f.read()
    
    def delete_agent_zip(self, agent_id: str):
        """Delete agent zip file"""
        file_path = self.storage_dir / f"{agent_id}.zip"
        if file_path.exists():
            file_path.unlink()
    
    def add_agent(self, agent: Agent, zip_data: bytes):
        """Add agent with zip file storage"""
        with Session(self.engine) as session:
            # Store zip file and update path
            agent.zip_file_path = self.store_agent_zip(agent.agent_id, zip_data)
            session.add(agent)
            session.commit()
    
    def delete_agent(self, agent_id: str):
        """Delete agent and its zip file"""
        with Session(self.engine) as session:
            agent = session.get(Agent, agent_id)
            if agent:
                self.delete_agent_zip(agent_id)
                session.delete(agent)
                session.commit()
    
    def add_codegen_challenge(self, codegen_challenge: CodegenChallenge):
        with Session(self.engine) as session:
            session.add(codegen_challenge)
            session.commit()
    
    def add_challenge(self, challenge: Challenge):
        with Session(self.engine) as session:
            session.add(challenge)
            session.commit()
