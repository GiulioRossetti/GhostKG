"""
SQLAlchemy ORM models for GhostKG database.

This module defines the declarative models for the knowledge graph database,
supporting SQLite, PostgreSQL, and MySQL through SQLAlchemy.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Node(Base):
    """
    Knowledge graph node (entity) with FSRS memory state.
    
    Represents concepts, people, topics with spaced repetition tracking.
    Multi-tenant via owner_id.
    """
    __tablename__ = "nodes"
    
    # Composite primary key for multi-tenancy
    owner_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    
    # FSRS memory state
    stability: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
    difficulty: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
    last_review: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reps: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    state: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.current_timestamp(),
        server_default=func.current_timestamp()
    )
    
    # Simulation time (round-based)
    sim_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sim_hour: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index("idx_nodes_owner", "owner_id"),
        Index("idx_nodes_last_review", "owner_id", "last_review"),
    )
    
    def __repr__(self):
        return f"<Node(owner_id='{self.owner_id}', id='{self.id}')>"


class Edge(Base):
    """
    Knowledge graph edge (relationship) between entities.
    
    Represents triplets (source, relation, target) with sentiment scoring.
    Multi-tenant via owner_id.
    """
    __tablename__ = "edges"
    
    # Composite primary key
    owner_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    source: Mapped[str] = mapped_column(String(255), primary_key=True)
    target: Mapped[str] = mapped_column(String(255), primary_key=True)
    relation: Mapped[str] = mapped_column(String(255), primary_key=True)
    
    # Edge properties
    weight: Mapped[float] = mapped_column(Float, default=1.0, server_default="1.0")
    sentiment: Mapped[float] = mapped_column(
        Float, 
        default=0.0, 
        server_default="0.0",
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.current_timestamp(),
        server_default=func.current_timestamp()
    )
    
    # Simulation time (round-based)
    sim_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sim_hour: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Foreign keys to nodes (both source and target must exist)
    __table_args__ = (
        ForeignKeyConstraint(
            ["owner_id", "source"],
            ["nodes.owner_id", "nodes.id"],
            name="fk_edges_source"
        ),
        ForeignKeyConstraint(
            ["owner_id", "target"],
            ["nodes.owner_id", "nodes.id"],
            name="fk_edges_target"
        ),
        CheckConstraint(
            "sentiment >= -1.0 AND sentiment <= 1.0",
            name="ck_edges_sentiment_range"
        ),
        Index("idx_edges_owner_source", "owner_id", "source"),
        Index("idx_edges_owner_target", "owner_id", "target"),
        Index("idx_edges_created", "owner_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<Edge(owner_id='{self.owner_id}', {self.source} --{self.relation}--> {self.target})>"


class Log(Base):
    """
    Agent interaction log for debugging and analysis.
    
    Records agent actions with optional content storage (UUID-based archiving).
    """
    __tablename__ = "logs"
    
    # Auto-incrementing primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Agent and action metadata
    agent_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    action_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Content storage (either content or content_uuid)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_uuid: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Annotations (JSON)
    annotations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.current_timestamp(),
        server_default=func.current_timestamp()
    )
    
    # Simulation time (round-based)
    sim_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sim_hour: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index("idx_logs_agent_time", "agent_name", "timestamp"),
        Index("idx_logs_action", "action_type", "timestamp"),
    )
    
    def __repr__(self):
        return f"<Log(id={self.id}, agent='{self.agent_name}', action='{self.action_type}')>"
