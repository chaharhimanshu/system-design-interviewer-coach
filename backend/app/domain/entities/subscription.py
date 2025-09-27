"""
Subscription Domain Entity
Contains business logic for subscription management
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID


class SubscriptionTier(Enum):
    """Subscription tier enumeration"""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(Enum):
    """User subscription status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class Subscription:
    """
    Subscription domain entity representing a subscription plan
    """
    id: UUID
    name: str
    tier: SubscriptionTier
    description: Optional[str]
    price: Decimal
    billing_cycle: str  # "monthly", "yearly", etc.
    interview_limit: int
    features: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization validation"""
        if self.price < 0:
            raise ValueError("Subscription price cannot be negative")
        
        if self.interview_limit < 0:
            raise ValueError("Interview limit cannot be negative")

    def is_free_tier(self) -> bool:
        """Check if this is a free tier subscription"""
        return self.tier == SubscriptionTier.FREE

    def is_premium_tier(self) -> bool:
        """Check if this is a premium tier subscription"""
        return self.tier == SubscriptionTier.PREMIUM

    def is_enterprise_tier(self) -> bool:
        """Check if this is an enterprise tier subscription"""
        return self.tier == SubscriptionTier.ENTERPRISE

    def has_unlimited_interviews(self) -> bool:
        """Check if subscription has unlimited interviews"""
        return self.interview_limit == -1

    def get_monthly_price(self) -> Decimal:
        """Get equivalent monthly price"""
        if self.billing_cycle == "yearly":
            return self.price / 12
        elif self.billing_cycle == "monthly":
            return self.price
        else:
            return self.price  # Default case


@dataclass
class UserSubscription:
    """
    User subscription domain entity representing a user's active subscription
    """
    id: UUID
    user_id: UUID
    subscription_id: UUID
    status: SubscriptionStatus
    start_date: datetime
    end_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization validation"""
        if self.end_date and self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")

    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        if self.status != SubscriptionStatus.ACTIVE:
            return False
        
        now = datetime.now(timezone.utc)
        
        # Check if subscription has started
        if self.start_date > now:
            return False
        
        # Check if subscription has expired
        if self.end_date and self.end_date <= now:
            return False
        
        return True

    def is_expired(self) -> bool:
        """Check if subscription has expired"""
        if not self.end_date:
            return False  # No end date means it doesn't expire
        
        return datetime.now(timezone.utc) >= self.end_date

    def days_until_expiry(self) -> Optional[int]:
        """Get number of days until subscription expires"""
        if not self.end_date:
            return None  # No expiry date
        
        now = datetime.now(timezone.utc)
        if self.end_date <= now:
            return 0  # Already expired
        
        delta = self.end_date - now
        return delta.days

    def extend_subscription(self, days: int) -> None:
        """Extend subscription by specified number of days"""
        if days <= 0:
            raise ValueError("Extension days must be positive")
        
        if not self.end_date:
            # If no end date, set it to current time + extension
            self.end_date = datetime.now(timezone.utc) + timedelta(days=days)
        else:
            # Extend existing end date
            self.end_date += timedelta(days=days)

    def cancel_subscription(self) -> None:
        """Cancel the subscription"""
        self.status = SubscriptionStatus.CANCELLED
        self.updated_at = datetime.now(timezone.utc)

    def reactivate_subscription(self) -> None:
        """Reactivate a cancelled subscription"""
        if self.status == SubscriptionStatus.CANCELLED:
            self.status = SubscriptionStatus.ACTIVE
            self.updated_at = datetime.now(timezone.utc)
        else:
            raise ValueError("Can only reactivate cancelled subscriptions")


@dataclass
class UserSubscriptionDetails:
    """
    Combined user subscription details with joined data
    """
    # User information
    user_id: UUID
    user_email: str
    user_name: str
    user_created_at: datetime
    
    # Subscription information
    subscription_id: UUID
    subscription_name: str
    subscription_tier: SubscriptionTier
    subscription_price: Decimal
    subscription_billing_cycle: str
    subscription_interview_limit: int
    
    # User subscription information
    user_subscription_id: UUID
    user_subscription_status: SubscriptionStatus
    user_subscription_start_date: datetime
    user_subscription_end_date: Optional[datetime]
    
    def is_subscription_active(self) -> bool:
        """Check if the user's subscription is currently active"""
        return (
            self.user_subscription_status == SubscriptionStatus.ACTIVE and
            self.user_subscription_start_date <= datetime.now(timezone.utc) and
            (not self.user_subscription_end_date or 
             self.user_subscription_end_date > datetime.now(timezone.utc))
        )
    
    def get_interviews_remaining(self, interviews_used: int) -> int:
        """Calculate remaining interviews for this billing period"""
        if self.subscription_interview_limit == -1:  # Unlimited
            return -1
        
        return max(0, self.subscription_interview_limit - interviews_used)