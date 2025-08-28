"""
User Domain Entities for System Design Interview Coach
Scalable design with future payment integration support
"""

from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum
import uuid
from dataclasses import dataclass


class UserStatus(str, Enum):
    """User account status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class SubscriptionTier(str, Enum):
    """User subscription tiers - ready for payment integration"""

    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class UserRole(str, Enum):
    """User roles for authorization"""

    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


@dataclass
class UserProfile:
    """User profile value object"""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None  # Encrypted in database
    company: Optional[str] = None
    job_title: Optional[str] = None
    years_of_experience: Optional[int] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


@dataclass
class UserPreferences:
    """User preferences and settings"""

    preferred_topics: List[str] = None
    difficulty_level: str = "intermediate"  # beginner, intermediate, advanced
    session_duration_preference: int = 45  # minutes
    email_notifications: bool = True
    push_notifications: bool = True
    timezone: str = "UTC"

    def __post_init__(self):
        if self.preferred_topics is None:
            self.preferred_topics = []


@dataclass
class SubscriptionDetails:
    """Subscription details - ready for payment integration"""

    tier: SubscriptionTier
    started_at: datetime
    expires_at: Optional[datetime] = None
    is_trial: bool = False
    trial_ends_at: Optional[datetime] = None
    auto_renew: bool = True
    payment_method_id: Optional[str] = None  # For future Stripe integration

    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        now = datetime.now(timezone.utc)
        if self.expires_at:
            return now < self.expires_at
        return True

    @property
    def days_remaining(self) -> Optional[int]:
        """Days remaining in subscription"""
        if not self.expires_at:
            return None
        now = datetime.now(timezone.utc)
        delta = self.expires_at - now
        return max(0, delta.days)


class User:
    """
    User domain entity - main aggregate root
    Follows DDD principles with rich domain logic
    """

    def __init__(
        self,
        user_id: uuid.UUID,
        email: str,
        google_id: str,
        status: UserStatus = UserStatus.ACTIVE,
        role: UserRole = UserRole.USER,
        profile: Optional[UserProfile] = None,
        preferences: Optional[UserPreferences] = None,
        subscription: Optional[SubscriptionDetails] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        last_login_at: Optional[datetime] = None,
        email_verified: bool = False,
        terms_accepted_at: Optional[datetime] = None,
        privacy_accepted_at: Optional[datetime] = None,
    ):
        self.user_id = user_id
        self.email = email
        self.google_id = google_id
        self.status = status
        self.role = role
        self.profile = profile or UserProfile()
        self.preferences = preferences or UserPreferences()
        self.subscription = subscription or SubscriptionDetails(
            tier=SubscriptionTier.FREE, started_at=datetime.now(timezone.utc)
        )
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.last_login_at = last_login_at
        self.email_verified = email_verified
        self.terms_accepted_at = terms_accepted_at
        self.privacy_accepted_at = privacy_accepted_at

        # Domain events (for future event-driven architecture)
        self._domain_events: List = []

    def update_profile(self, profile_data: dict) -> None:
        """Update user profile with validation"""
        allowed_fields = {
            "first_name",
            "last_name",
            "phone_number",
            "company",
            "job_title",
            "years_of_experience",
            "bio",
            "avatar_url",
        }

        for field, value in profile_data.items():
            if field in allowed_fields and hasattr(self.profile, field):
                setattr(self.profile, field, value)

        self._mark_as_updated()

    def update_preferences(self, preferences_data: dict) -> None:
        """Update user preferences"""
        allowed_fields = {
            "preferred_topics",
            "difficulty_level",
            "session_duration_preference",
            "email_notifications",
            "push_notifications",
            "timezone",
        }

        for field, value in preferences_data.items():
            if field in allowed_fields and hasattr(self.preferences, field):
                setattr(self.preferences, field, value)

        self._mark_as_updated()

    def upgrade_subscription(
        self,
        tier: SubscriptionTier,
        duration_months: int = 1,
        payment_method_id: Optional[str] = None,
    ) -> None:
        """Upgrade user subscription - ready for payment integration"""
        from dateutil.relativedelta import relativedelta

        now = datetime.now(timezone.utc)
        expires_at = now + relativedelta(months=duration_months)

        self.subscription = SubscriptionDetails(
            tier=tier,
            started_at=now,
            expires_at=expires_at,
            payment_method_id=payment_method_id,
            auto_renew=True,
        )

        self._mark_as_updated()
        # TODO: Add domain event for subscription upgrade

    def start_trial(self, tier: SubscriptionTier, trial_days: int = 14) -> None:
        """Start trial subscription"""
        from dateutil.relativedelta import relativedelta

        now = datetime.now(timezone.utc)
        trial_ends_at = now + relativedelta(days=trial_days)

        self.subscription = SubscriptionDetails(
            tier=tier,
            started_at=now,
            expires_at=trial_ends_at,
            is_trial=True,
            trial_ends_at=trial_ends_at,
            auto_renew=False,
        )

        self._mark_as_updated()

    def deactivate(self, reason: Optional[str] = None) -> None:
        """Deactivate user account"""
        self.status = UserStatus.INACTIVE
        self._mark_as_updated()
        # TODO: Add domain event for user deactivation

    def suspend(self, reason: Optional[str] = None) -> None:
        """Suspend user account"""
        self.status = UserStatus.SUSPENDED
        self._mark_as_updated()
        # TODO: Add domain event for user suspension

    def mark_login(self) -> None:
        """Mark user as logged in"""
        self.last_login_at = datetime.now(timezone.utc)
        self._mark_as_updated()

    def verify_email(self) -> None:
        """Mark email as verified"""
        self.email_verified = True
        self._mark_as_updated()

    def accept_terms(self) -> None:
        """Mark terms as accepted"""
        self.terms_accepted_at = datetime.now(timezone.utc)
        self._mark_as_updated()

    def accept_privacy(self) -> None:
        """Mark privacy policy as accepted"""
        self.privacy_accepted_at = datetime.now(timezone.utc)
        self._mark_as_updated()

    def can_access_feature(self, feature: str) -> bool:
        """Check if user can access a feature based on subscription"""
        feature_access = {
            SubscriptionTier.FREE: {"basic_interviews", "limited_sessions"},
            SubscriptionTier.PREMIUM: {
                "basic_interviews",
                "unlimited_sessions",
                "advanced_feedback",
                "hld_diagrams",
                "progress_tracking",
            },
            SubscriptionTier.ENTERPRISE: {
                "basic_interviews",
                "unlimited_sessions",
                "advanced_feedback",
                "hld_diagrams",
                "progress_tracking",
                "team_management",
                "custom_topics",
                "api_access",
            },
        }

        allowed_features = feature_access.get(self.subscription.tier, set())
        return feature in allowed_features

    def get_session_limits(self) -> dict:
        """Get session limits based on subscription"""
        limits = {
            SubscriptionTier.FREE: {
                "sessions_per_day": 2,
                "sessions_per_month": 10,
                "max_session_duration": 30,  # minutes
            },
            SubscriptionTier.PREMIUM: {
                "sessions_per_day": 10,
                "sessions_per_month": -1,  # unlimited
                "max_session_duration": 60,
            },
            SubscriptionTier.ENTERPRISE: {
                "sessions_per_day": -1,  # unlimited
                "sessions_per_month": -1,
                "max_session_duration": 90,
            },
        }

        return limits.get(self.subscription.tier, limits[SubscriptionTier.FREE])

    def _mark_as_updated(self) -> None:
        """Mark entity as updated"""
        self.updated_at = datetime.now(timezone.utc)

    def __eq__(self, other) -> bool:
        if not isinstance(other, User):
            return False
        return self.user_id == other.user_id

    def __hash__(self) -> int:
        return hash(self.user_id)

    def __repr__(self) -> str:
        return f"User(user_id={self.user_id}, email={self.email}, status={self.status})"
