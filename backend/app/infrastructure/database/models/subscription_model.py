"""
SQLAlchemy Subscription Models
Database representation of subscription-related entities
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
    Numeric,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class SubscriptionModel(Base):
    """SQLAlchemy Subscription model"""

    __tablename__ = "subscriptions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Subscription details
    tier = Column(
        Enum(
            "free",
            "premium", 
            "enterprise",
            name="subscription_tier",
            create_type=False,  # Use existing PostgreSQL enum
        ),
        nullable=False,
    )
    details = Column(Text)
    pricing = Column(Numeric(10, 2), nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<SubscriptionModel(id={self.id}, tier={self.tier}, pricing={self.pricing})>"


class UserSubscriptionModel(Base):
    """SQLAlchemy User Subscription model - junction table between users and subscriptions"""

    __tablename__ = "user_subscriptions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Subscription period
    start_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    end_date = Column(DateTime(timezone=True))

    # Status
    status = Column(
        Enum(
            "active",
            "inactive",
            "expired", 
            "cancelled",
            name="subscription_status",
            create_type=False,  # Use existing PostgreSQL enum
        ),
        nullable=False,
        default="active",
        index=True,
    )

    # Relationships
    user = relationship("UserModel", backref="user_subscriptions")
    subscription = relationship("SubscriptionModel", backref="user_subscriptions")

    # Indexes for performance
    __table_args__ = (
        Index("idx_user_subscriptions_user_status", "user_id", "status"),
        Index("idx_user_subscriptions_dates", "start_date", "end_date"),
    )

    def __repr__(self) -> str:
        return f"<UserSubscriptionModel(id={self.id}, user_id={self.user_id}, status={self.status})>"