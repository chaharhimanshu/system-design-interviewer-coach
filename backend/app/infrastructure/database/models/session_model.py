"""
SQLAlchemy Session Model
Database representation of Interview Session entity
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    Text,
    Enum,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base
from app.domain.entities.session import (
    InterviewSession,
    SessionConfig,
    SessionStatus,
    DifficultyLevel,
)


class SessionModel(Base):
    """SQLAlchemy Session model"""

    __tablename__ = "sessions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to user
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Session configuration
    topic = Column(String(200), nullable=False, index=True)
    difficulty_level = Column(
        Enum(
            DifficultyLevel,
            name="difficulty_level",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=DifficultyLevel.INTERMEDIATE.value,
    )
    max_duration_minutes = Column(Integer, nullable=False, default=60)
    enable_hints = Column(Boolean, nullable=False, default=True)
    enable_real_time_feedback = Column(Boolean, nullable=False, default=True)
    custom_requirements = Column(Text)

    # Session status and timing
    status = Column(
        Enum(
            SessionStatus,
            name="session_status",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=SessionStatus.ACTIVE.value,
        index=True,
    )
    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    ended_at = Column(DateTime(timezone=True))
    total_duration = Column(Integer)  # in seconds

    # Session metadata
    session_config = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    messages = relationship(
        "MessageModel", back_populates="session", cascade="all, delete-orphan"
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_sessions_user_status", "user_id", "status"),
        Index("idx_sessions_topic", "topic"),
        Index("idx_sessions_started_at", "started_at"),
        Index("idx_sessions_difficulty", "difficulty_level"),
    )

    def to_entity(self) -> InterviewSession:
        """Convert SQLAlchemy model to domain entity"""
        # Create session config
        config = SessionConfig(
            topic=self.topic,
            difficulty_level=DifficultyLevel(self.difficulty_level),
            max_duration_minutes=self.max_duration_minutes,
            enable_hints=self.enable_hints,
            enable_real_time_feedback=self.enable_real_time_feedback,
            custom_requirements=self.custom_requirements,
        )

        # Create session entity
        session = InterviewSession(
            session_id=self.id,
            user_id=self.user_id,
            config=config,
            status=SessionStatus(self.status),
            started_at=self.started_at,
            ended_at=self.ended_at,
            total_duration=self.total_duration,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

        # Add messages if loaded
        if hasattr(self, "messages") and self.messages:
            for message_model in self.messages:
                message = message_model.to_entity()
                session.messages.append(message)

        return session

    @classmethod
    def from_entity(cls, session: InterviewSession) -> "SessionModel":
        """Create SQLAlchemy model from domain entity"""
        return cls(
            id=session.session_id,
            user_id=session.user_id,
            topic=session.config.topic,
            difficulty_level=session.config.difficulty_level.value,
            max_duration_minutes=session.config.max_duration_minutes,
            enable_hints=session.config.enable_hints,
            enable_real_time_feedback=session.config.enable_real_time_feedback,
            custom_requirements=session.config.custom_requirements,
            status=session.status.value,
            started_at=session.started_at,
            ended_at=session.ended_at,
            total_duration=session.total_duration,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    def update_from_entity(self, session: InterviewSession) -> None:
        """Update model fields from domain entity"""
        self.topic = session.config.topic
        self.difficulty_level = session.config.difficulty_level.value
        self.max_duration_minutes = session.config.max_duration_minutes
        self.enable_hints = session.config.enable_hints
        self.enable_real_time_feedback = session.config.enable_real_time_feedback
        self.custom_requirements = session.config.custom_requirements
        self.status = session.status.value
        self.started_at = session.started_at
        self.ended_at = session.ended_at
        self.total_duration = session.total_duration
        self.updated_at = session.updated_at

    def __repr__(self) -> str:
        return f"<SessionModel(id={self.id}, topic={self.topic}, status={self.status})>"
