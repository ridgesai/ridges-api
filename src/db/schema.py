from datetime import datetime
from typing import List
from pathlib import Path
import logging

from sqlalchemy import ForeignKey, Integer, String, DateTime, Boolean, Float, LargeBinary, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session,mapped_column, relationship

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

class Challenge(Base):
    __tablename__ = "challenge_table"

    challenge_id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    validator_hotkey: Mapped[str] = mapped_column(String, nullable=False)

    # Add discriminator column for polymorphic inheritance
    type: Mapped[str] = mapped_column(String, nullable=False)

    codegen_challenges: Mapped["CodegenChallenge"] = relationship(back_populates="challenge")
    regression_challenges: Mapped["RegressionChallenge"] = relationship(back_populates="challenge")
    responses: Mapped[List["Response"]] = relationship(back_populates="challenge")

    __mapper_args__ = {
        "polymorphic_identity": "challenge",
        "polymorphic_on": type
    }

class CodegenChallenge(Challenge):
    __tablename__ = "codegen_challenge_table"

    challenge_id: Mapped[str] = mapped_column(String, ForeignKey("challenge_table.challenge_id"), primary_key=True)
    problem_statement: Mapped[str] = mapped_column(String, nullable=False)
    dynamic_checklist: Mapped[str] = mapped_column(String, nullable=False)
    repository_url: Mapped[str] = mapped_column(String, nullable=False)
    commit_hash: Mapped[str] = mapped_column(String, nullable=True)
    context_file_paths: Mapped[str] = mapped_column(String, nullable=False)

    challenge: Mapped["Challenge"] = relationship(back_populates="codegen_challenges")

    __mapper_args__ = {
        "polymorphic_identity": "codegen",
        "inherit_condition": challenge_id == Challenge.challenge_id
    }

class RegressionChallenge(Challenge):
    __tablename__ = "regression_challenge_table"

    challenge_id: Mapped[str] = mapped_column(String, ForeignKey("challenge_table.challenge_id"), primary_key=True)
    problem_statement: Mapped[str] = mapped_column(String, nullable=False)
    repository_url: Mapped[str] = mapped_column(String, nullable=False)
    commit_hash: Mapped[str] = mapped_column(String, nullable=True)
    context_file_paths: Mapped[str] = mapped_column(String, nullable=False)

    challenge: Mapped["Challenge"] = relationship(back_populates="regression_challenges")

    __mapper_args__ = {
        "polymorphic_identity": "regression",
        "inherit_condition": challenge_id == Challenge.challenge_id
    }

class Agent(Base):
    __tablename__ = "agent_table"

    agent_id: Mapped[str] = mapped_column(String, primary_key=True)
    miner_hotkey: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    elo: Mapped[int] = mapped_column(Integer, nullable=False)
    num_responses: Mapped[int] = mapped_column(Integer, nullable=False)

    responses: Mapped[List["Response"]] = relationship(back_populates="agent")

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
    
    # Add discriminator column for polymorphic inheritance
    type: Mapped[str] = mapped_column(String, nullable=False)

    challenge: Mapped["Challenge"] = relationship(back_populates="responses")
    agent: Mapped["Agent"] = relationship(back_populates="responses")

    __mapper_args__ = {
        "polymorphic_identity": "response",
        "polymorphic_on": type
    }

class CodegenResponse(Response):
    __tablename__ = "codegen_response_table"
    
    challenge_id: Mapped[str] = mapped_column(String, ForeignKey("response_table.challenge_id"), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String, ForeignKey("response_table.agent_id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": "codegen",
        "inherit_condition": (challenge_id == Response.challenge_id) & (agent_id == Response.agent_id)
    }

class RegressionResponse(Response):
    __tablename__ = "regression_response_table"
    
    challenge_id: Mapped[str] = mapped_column(String, ForeignKey("response_table.challenge_id"), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String, ForeignKey("response_table.agent_id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": "regression",
        "inherit_condition": (challenge_id == Response.challenge_id) & (agent_id == Response.agent_id)
    }
