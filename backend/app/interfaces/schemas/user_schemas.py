"""
User Pydantic Schemas for API Request/Response
Handles serialization/deserialization for user-related endpoints
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.domain.entities.user import User, UserStatus, UserRole, SubscriptionTier


class UserProfileSchema(BaseModel):
    """User profile schema"""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    years_of_experience: Optional[int] = Field(None, ge=0, le=50)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None


class UserPreferencesSchema(BaseModel):
    """User preferences schema"""

    preferred_topics: List[str] = Field(default_factory=list)
    difficulty_level: str = Field(
        default="intermediate", pattern="^(beginner|intermediate|advanced)$"
    )
    session_duration_preference: int = Field(default=45, ge=15, le=90)
    email_notifications: bool = True
    push_notifications: bool = True
    timezone: str = "UTC"


class SubscriptionSchema(BaseModel):
    """Subscription details schema"""

    tier: SubscriptionTier
    started_at: datetime
    expires_at: Optional[datetime] = None
    is_trial: bool = False
    trial_ends_at: Optional[datetime] = None
    auto_renew: bool = True
    is_active: bool
    days_remaining: Optional[int] = None


class UserResponse(BaseModel):
    """User response schema for API responses"""

    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    email: EmailStr
    status: UserStatus
    role: UserRole
    profile: UserProfileSchema
    preferences: UserPreferencesSchema
    subscription: SubscriptionSchema
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    email_verified: bool
    terms_accepted_at: Optional[datetime] = None
    privacy_accepted_at: Optional[datetime] = None

    @classmethod
    def from_entity(cls, user: User) -> "UserResponse":
        """Convert User entity to response schema"""
        return cls(
            user_id=user.user_id,
            email=user.email,
            status=user.status,
            role=user.role,
            profile=UserProfileSchema(
                first_name=user.profile.first_name,
                last_name=user.profile.last_name,
                phone_number=user.profile.phone_number,
                company=user.profile.company,
                job_title=user.profile.job_title,
                years_of_experience=user.profile.years_of_experience,
                bio=user.profile.bio,
                avatar_url=user.profile.avatar_url,
            ),
            preferences=UserPreferencesSchema(
                preferred_topics=user.preferences.preferred_topics,
                difficulty_level=user.preferences.difficulty_level,
                session_duration_preference=user.preferences.session_duration_preference,
                email_notifications=user.preferences.email_notifications,
                push_notifications=user.preferences.push_notifications,
                timezone=user.preferences.timezone,
            ),
            subscription=SubscriptionSchema(
                tier=user.subscription.tier,
                started_at=user.subscription.started_at,
                expires_at=user.subscription.expires_at,
                is_trial=user.subscription.is_trial,
                trial_ends_at=user.subscription.trial_ends_at,
                auto_renew=user.subscription.auto_renew,
                is_active=user.subscription.is_active,
                days_remaining=user.subscription.days_remaining,
            ),
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
            email_verified=user.email_verified,
            terms_accepted_at=user.terms_accepted_at,
            privacy_accepted_at=user.privacy_accepted_at,
        )


class UserProfileUpdate(BaseModel):
    """User profile update request schema"""

    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone_number: Optional[str] = Field(None, pattern=r"^\+?[\d\s\-\(\)]{7,20}$")
    company: Optional[str] = Field(None, min_length=1, max_length=100)
    job_title: Optional[str] = Field(None, min_length=1, max_length=100)
    years_of_experience: Optional[int] = Field(None, ge=0, le=50)
    bio: Optional[str] = Field(None, max_length=500)


class UserPreferencesUpdate(BaseModel):
    """User preferences update request schema"""

    preferred_topics: Optional[List[str]] = None
    difficulty_level: Optional[str] = Field(
        None, pattern="^(beginner|intermediate|advanced)$"
    )
    session_duration_preference: Optional[int] = Field(None, ge=15, le=90)
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    timezone: Optional[str] = None


class GoogleAuthRequest(BaseModel):
    """Google OAuth authentication request"""

    access_token: str = Field(..., min_length=1)
    id_token: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""

    refresh_token: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Token response schema"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse


class UserListResponse(BaseModel):
    """User list response with pagination"""

    users: List[UserResponse]
    total: int
    offset: int
    limit: int
    has_more: bool


class SubscriptionUpgradeRequest(BaseModel):
    """Subscription upgrade request"""

    tier: SubscriptionTier
    duration_months: int = Field(default=1, ge=1, le=24)
    payment_method_id: Optional[str] = None  # For future Stripe integration


class TrialStartRequest(BaseModel):
    """Trial start request"""

    tier: SubscriptionTier
    trial_days: int = Field(default=14, ge=1, le=30)
