"""
SQLAlchemy Interview Tool Model
Database representation of interview tools
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.database.base import Base


class InterviewToolModel(Base):
    """SQLAlchemy Interview Tool model"""

    __tablename__ = "interview_tools"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Tool details
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<InterviewToolModel(id={self.id}, name={self.name})>"