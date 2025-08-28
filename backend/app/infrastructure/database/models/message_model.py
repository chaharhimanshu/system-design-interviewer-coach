"""
SQLAlchemy Message Model
Database representation of chat messages in interview sessions
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column,
    String,
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
    Message,
    MessageRole,
    MessageType,
)


class MessageModel(Base):
    """SQLAlchemy Message model"""

    __tablename__ = "messages"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to session
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message content and metadata
    role = Column(
        Enum(
            MessageRole,
            name="message_role",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        index=True,
    )
    content = Column(Text, nullable=False)
    message_type = Column(
        Enum(
            MessageType,
            name="message_type",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=MessageType.TEXT.value,
    )

    # Message timing and usage
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    tokens_used = Column(Integer, nullable=False, default=0)

    # Flexible metadata storage
    message_metadata = Column(JSON, nullable=False, default=dict)

    # Relationship back to session
    session = relationship("SessionModel", back_populates="messages")

    # Indexes for performance
    __table_args__ = (
        Index("idx_messages_session_timestamp", "session_id", "timestamp"),
        Index("idx_messages_role", "role"),
        Index("idx_messages_type", "message_type"),
    )

    def to_entity(self) -> Message:
        """Convert SQLAlchemy model to domain entity"""
        return Message(
            message_id=self.id,
            role=MessageRole(self.role),
            content=self.content,
            message_type=MessageType(self.message_type),
            timestamp=self.timestamp,
            metadata=self.message_metadata or {},
            tokens_used=self.tokens_used,
        )

    @classmethod
    def from_entity(cls, message: Message, session_id: uuid.UUID) -> "MessageModel":
        """Create SQLAlchemy model from domain entity"""
        return cls(
            id=message.message_id,
            session_id=session_id,
            role=message.role.value,
            content=message.content,
            message_type=message.message_type.value,
            timestamp=message.timestamp,
            message_metadata=message.metadata,
            tokens_used=message.tokens_used,
        )

    def update_from_entity(self, message: Message) -> None:
        """Update model fields from domain entity"""
        self.role = message.role.value
        self.content = message.content
        self.message_type = message.message_type.value
        self.timestamp = message.timestamp
        self.message_metadata = message.metadata
        self.tokens_used = message.tokens_used

    def __repr__(self) -> str:
        return f"<MessageModel(id={self.id}, session_id={self.session_id}, role={self.role})>"
