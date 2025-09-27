"""
SQLAlchemy Topic Model
Database representation of interview topics
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    Enum,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class TopicModel(Base):
    """SQLAlchemy Topic model"""

    __tablename__ = "topics"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to interview tool
    tool_id = Column(
        UUID(as_uuid=True),
        ForeignKey("interview_tools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Topic details
    topic_name = Column(String(200), nullable=False)
    type = Column(
        Enum(
            "system",
            "user",
            name="topic_type",
            create_type=False,  # Use existing PostgreSQL enum
        ),
        nullable=False,
        default="system",
    )
    topic_description = Column(Text)
    topic_data = Column(JSONB, default=dict)
    level = Column(
        Enum(
            "beginner",
            "intermediate", 
            "advanced",
            name="topic_level",
            create_type=False,  # Use existing PostgreSQL enum
        ),
        nullable=False,
        default="intermediate",
    )

    # Relationship to interview tool
    interview_tool = relationship("InterviewToolModel", backref="topics")

    # Indexes for performance
    __table_args__ = (
        Index("idx_topics_tool_id", "tool_id"),
        Index("idx_topics_name_level", "topic_name", "level"),
        Index("idx_topics_type", "type"),
    )

    def __repr__(self) -> str:
        return f"<TopicModel(id={self.id}, name={self.topic_name}, level={self.level})>"