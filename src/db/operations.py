from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from db.schema import Agent, CodegenChallenge, Challenge, Base

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
