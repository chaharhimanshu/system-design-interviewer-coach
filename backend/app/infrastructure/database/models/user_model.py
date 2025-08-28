"""
SQLAlchemy User Model
Database representation of User entity with encryption support
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
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from cryptography.fernet import Fernet
import os

from app.infrastructure.database.base import Base
from app.domain.entities.user import (
    User,
    UserProfile,
    UserPreferences,
    SubscriptionDetails,
    UserStatus,
    UserRole,
    SubscriptionTier,
)


# Encryption key for sensitive data (should be from environment)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)


class UserModel(Base):
    """SQLAlchemy User model with encryption support"""

    __tablename__ = "users"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Authentication fields
    email = Column(String(255), nullable=False, unique=True, index=True)
    google_id = Column(String(255), nullable=False, unique=True, index=True)

    # User status and role
    status = Column(
        Enum(
            UserStatus,
            name="user_status",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=UserStatus.ACTIVE.value,
        index=True,
    )
    role = Column(
        Enum(
            UserRole,
            name="user_role",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=UserRole.USER.value,
    )

    # Profile fields (some encrypted)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone_number_encrypted = Column(Text)  # Encrypted field
    company = Column(String(100))
    job_title = Column(String(100))
    years_of_experience = Column(Integer)
    bio = Column(Text)
    avatar_url = Column(String(500))

    # Preferences (stored as JSON)
    preferences = Column(JSON, nullable=False, default=dict)

    # Subscription details (stored as JSON)
    subscription_data = Column(JSON, nullable=False, default=dict)

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
    last_login_at = Column(DateTime(timezone=True))

    # Verification and compliance
    email_verified = Column(Boolean, default=False, nullable=False)
    terms_accepted_at = Column(DateTime(timezone=True))
    privacy_accepted_at = Column(DateTime(timezone=True))

    # Indexes for performance
    __table_args__ = (
        Index("idx_users_email_status", "email", "status"),
        Index("idx_users_google_id", "google_id"),
        Index("idx_users_created_at", "created_at"),
        Index("idx_users_subscription_tier", "subscription_data"),
    )

    @hybrid_property
    def phone_number(self) -> Optional[str]:
        """Decrypt phone number"""
        if not self.phone_number_encrypted:
            return None
        try:
            return cipher_suite.decrypt(self.phone_number_encrypted.encode()).decode()
        except:
            return None

    @phone_number.setter
    def phone_number(self, value: Optional[str]) -> None:
        """Encrypt phone number"""
        if value is None:
            self.phone_number_encrypted = None
        else:
            self.phone_number_encrypted = cipher_suite.encrypt(value.encode()).decode()

    def to_entity(self) -> User:
        """Convert SQLAlchemy model to domain entity"""
        # Parse preferences
        preferences_data = self.preferences or {}
        preferences = UserPreferences(
            preferred_topics=preferences_data.get("preferred_topics", []),
            difficulty_level=preferences_data.get("difficulty_level", "intermediate"),
            session_duration_preference=preferences_data.get(
                "session_duration_preference", 45
            ),
            email_notifications=preferences_data.get("email_notifications", True),
            push_notifications=preferences_data.get("push_notifications", True),
            timezone=preferences_data.get("timezone", "UTC"),
        )

        # Parse subscription
        sub_data = self.subscription_data or {}
        subscription = SubscriptionDetails(
            tier=SubscriptionTier(sub_data.get("tier", "free")),
            started_at=datetime.fromisoformat(
                sub_data.get("started_at", self.created_at.isoformat())
            ),
            expires_at=(
                datetime.fromisoformat(sub_data["expires_at"])
                if sub_data.get("expires_at")
                else None
            ),
            is_trial=sub_data.get("is_trial", False),
            trial_ends_at=(
                datetime.fromisoformat(sub_data["trial_ends_at"])
                if sub_data.get("trial_ends_at")
                else None
            ),
            auto_renew=sub_data.get("auto_renew", True),
            payment_method_id=sub_data.get("payment_method_id"),
        )

        # Create profile
        profile = UserProfile(
            first_name=self.first_name,
            last_name=self.last_name,
            phone_number=self.phone_number,  # This uses the hybrid property (decrypts)
            company=self.company,
            job_title=self.job_title,
            years_of_experience=self.years_of_experience,
            bio=self.bio,
            avatar_url=self.avatar_url,
        )

        return User(
            user_id=self.id,
            email=self.email,
            google_id=self.google_id,
            status=self.status,
            role=self.role,
            profile=profile,
            preferences=preferences,
            subscription=subscription,
            created_at=self.created_at,
            updated_at=self.updated_at,
            last_login_at=self.last_login_at,
            email_verified=self.email_verified,
            terms_accepted_at=self.terms_accepted_at,
            privacy_accepted_at=self.privacy_accepted_at,
        )

    @classmethod
    def from_entity(cls, user: User) -> "UserModel":
        """Create SQLAlchemy model from domain entity"""
        # Serialize preferences
        preferences_data = {
            "preferred_topics": user.preferences.preferred_topics,
            "difficulty_level": user.preferences.difficulty_level,
            "session_duration_preference": user.preferences.session_duration_preference,
            "email_notifications": user.preferences.email_notifications,
            "push_notifications": user.preferences.push_notifications,
            "timezone": user.preferences.timezone,
        }

        # Serialize subscription
        subscription_data = {
            "tier": user.subscription.tier.value,
            "started_at": user.subscription.started_at.isoformat(),
            "expires_at": (
                user.subscription.expires_at.isoformat()
                if user.subscription.expires_at
                else None
            ),
            "is_trial": user.subscription.is_trial,
            "trial_ends_at": (
                user.subscription.trial_ends_at.isoformat()
                if user.subscription.trial_ends_at
                else None
            ),
            "auto_renew": user.subscription.auto_renew,
            "payment_method_id": user.subscription.payment_method_id,
        }

        model = cls(
            id=user.user_id,
            email=user.email,
            google_id=user.google_id,
            status=user.status.value,  # Use .value to get the enum value instead of enum name
            role=user.role.value,  # Use .value to get the enum value instead of enum name
            first_name=user.profile.first_name,
            last_name=user.profile.last_name,
            company=user.profile.company,
            job_title=user.profile.job_title,
            years_of_experience=user.profile.years_of_experience,
            bio=user.profile.bio,
            avatar_url=user.profile.avatar_url,
            preferences=preferences_data,
            subscription_data=subscription_data,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
            email_verified=user.email_verified,
            terms_accepted_at=user.terms_accepted_at,
            privacy_accepted_at=user.privacy_accepted_at,
        )

        # Set encrypted phone number
        model.phone_number = user.profile.phone_number

        return model

    def update_from_entity(self, user: User) -> None:
        """Update model fields from domain entity"""
        # Basic fields
        self.email = user.email
        self.status = user.status.value  # Use .value to get the enum value
        self.role = user.role.value  # Use .value to get the enum value
        self.updated_at = user.updated_at
        self.last_login_at = user.last_login_at
        self.email_verified = user.email_verified
        self.terms_accepted_at = user.terms_accepted_at
        self.privacy_accepted_at = user.privacy_accepted_at

        # Profile fields
        self.first_name = user.profile.first_name
        self.last_name = user.profile.last_name
        self.company = user.profile.company
        self.job_title = user.profile.job_title
        self.years_of_experience = user.profile.years_of_experience
        self.bio = user.profile.bio
        self.avatar_url = user.profile.avatar_url
        self.phone_number = user.profile.phone_number  # Uses setter (encrypts)

        # Preferences
        self.preferences = {
            "preferred_topics": user.preferences.preferred_topics,
            "difficulty_level": user.preferences.difficulty_level,
            "session_duration_preference": user.preferences.session_duration_preference,
            "email_notifications": user.preferences.email_notifications,
            "push_notifications": user.preferences.push_notifications,
            "timezone": user.preferences.timezone,
        }

        # Subscription
        self.subscription_data = {
            "tier": user.subscription.tier.value,
            "started_at": user.subscription.started_at.isoformat(),
            "expires_at": (
                user.subscription.expires_at.isoformat()
                if user.subscription.expires_at
                else None
            ),
            "is_trial": user.subscription.is_trial,
            "trial_ends_at": (
                user.subscription.trial_ends_at.isoformat()
                if user.subscription.trial_ends_at
                else None
            ),
            "auto_renew": user.subscription.auto_renew,
            "payment_method_id": user.subscription.payment_method_id,
        }

    def __repr__(self) -> str:
        return f"<UserModel(id={self.id}, email={self.email}, status={self.status})>"
