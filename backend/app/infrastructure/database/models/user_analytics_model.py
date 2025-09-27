"""
SQLAlchemy User Analytics Model
Database representation of user analytics and performance metrics
"""

import uuid
from datetime import datetime, timezone, date
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    Date,
    Numeric,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class UserAnalyticsModel(Base):
    """SQLAlchemy User Analytics model"""

    __tablename__ = "user_analytics"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to user (unique - one analytics record per user)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Performance metrics
    avg_score = Column(Numeric(5, 2))  # Average score from evaluations
    streak = Column(Integer, default=0)  # Consecutive days/sessions streak
    best_streak = Column(Integer, default=0)  # Best streak achieved
    total_interviews = Column(Integer, default=0)  # Total interviews ever completed

    # Interview tracking
    interviews_left = Column(Integer, default=0)  # Remaining interviews in current period
    interviews_this_month = Column(Integer, default=0)  # Interviews completed this month
    interviews_today = Column(Integer, default=0)  # Interviews completed today
    last_interview_date = Column(Date)  # Last interview date

    # Timestamps
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationship to user
    user = relationship("UserModel", backref="analytics")

    # Indexes for performance
    __table_args__ = (
        Index("idx_user_analytics_user_id", "user_id"),
        Index("idx_user_analytics_last_interview", "last_interview_date"),
    )

    def __repr__(self) -> str:
        return f"<UserAnalyticsModel(id={self.id}, user_id={self.user_id}, avg_score={self.avg_score})>"