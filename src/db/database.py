from datetime import datetime
from typing import List
from pathlib import Path
import logging

from sqlalchemy import ForeignKey, Integer, String, DateTime, Boolean, Float, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session,mapped_column, relationship

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

class Challenge(Base):
    __tablename__ = "challenge_table"

    challenge_id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    validator_hotkey: Mapped[str] = mapped_column(String, nullable=False)

    codegen_challenges: Mapped["CodegenChallenge"] = relationship(back_populates="challenge")
    responses: Mapped[List["Response"]] = relationship(back_populates="challenge")

class Agent(Base):
    __tablename__ = "agent_table"

    agent_id: Mapped[str] = mapped_column(String, primary_key=True)
    miner_hotkey: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    elo: Mapped[int] = mapped_column(Integer, nullable=False)
    num_responses: Mapped[int] = mapped_column(Integer, nullable=False)

    responses: Mapped[List["Response"]] = relationship(back_populates="agent")

class CodegenChallenge(Base):
    __tablename__ = "codegen_challenge_table"

    challenge_id: Mapped[str] = mapped_column(String, ForeignKey("challenge_table.challenge_id"), primary_key=True)
    validator_hotkey: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    problem_statement: Mapped[str] = mapped_column(String, nullable=False)
    dynamic_checklist: Mapped[str] = mapped_column(String, nullable=False)
    repository_url: Mapped[str] = mapped_column(String, nullable=False)
    commit_hash: Mapped[str] = mapped_column(String, nullable=True)
    context_file_paths: Mapped[str] = mapped_column(String, nullable=False)

    challenge: Mapped["Challenge"] = relationship(back_populates="codegen_challenges")

class Response(Base):
    __tablename__ = "response_table"

    challenge_id: Mapped[str] = mapped_column(String, ForeignKey("challenge_table.challenge_id"), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String, ForeignKey("agent_table.agent_id"), primary_key=True)
    miner_hotkey: Mapped[str] = mapped_column(String, nullable=False)
    node_id: Mapped[int] = mapped_column(Integer, nullable=True)
    processing_time: Mapped[float] = mapped_column(Float, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    evaluated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    response_patch: Mapped[str] = mapped_column(String, nullable=True)

    challenge: Mapped["Challenge"] = relationship(back_populates="responses")
    agent: Mapped["Agent"] = relationship(back_populates="responses")

if __name__ == "__main__":
    engine = create_engine("sqlite:///platform.db")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.commit()

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
