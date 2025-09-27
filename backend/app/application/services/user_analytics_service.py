"""
User Analytics Service
Handles user analytics operations and subscription limit checking
"""

from typing import Optional, Tuple
import uuid
from datetime import datetime, timezone

from app.domain.entities.user import User, SubscriptionTier
from app.domain.entities.user_analytics import UserAnalytics
from app.domain.repositories.user_analytics_repository import UserAnalyticsRepository
from app.shared.logging import get_logger

logger = get_logger(__name__)


class UserAnalyticsService:
    """Service for managing user analytics and interview limits"""

    def __init__(self, analytics_repository: UserAnalyticsRepository):
        self.analytics_repository = analytics_repository

    async def get_user_analytics(self, user_id: uuid.UUID) -> UserAnalytics:
        """Get or create user analytics"""
        return await self.analytics_repository.get_or_create(user_id)

    async def can_create_interview(self, user: User) -> Tuple[bool, str]:
        """Check if user can create a new interview based on subscription limits"""
        analytics = await self.get_user_analytics(user.user_id)
        limits = user.get_session_limits()
        max_interviews = limits.get("interviews_per_month", 0)

        # Unlimited interviews for premium users
        if max_interviews == -1:
            return True, "Unlimited interviews available"

        # Check monthly limit
        if not analytics.can_start_interview(max_interviews):
            if user.subscription.tier == SubscriptionTier.FREE:
                return (
                    False,
                    f"Free plan limit reached ({max_interviews} interviews per month). Upgrade to Premium for unlimited interviews!",
                )
            return False, f"Monthly limit of {max_interviews} interviews reached"

        remaining = analytics.get_remaining_interviews(max_interviews)
        return True, f"{remaining} interviews remaining this month"

    async def record_interview_started(self, user_id: uuid.UUID) -> UserAnalytics:
        """Record that user started a new interview"""
        analytics = await self.get_user_analytics(user_id)
        analytics.record_interview()
        
        updated_analytics = await self.analytics_repository.update(analytics)
        
        logger.info(
            f"Interview recorded for user {user_id}",
            extra={
                "user_id": str(user_id),
                "interviews_this_month": analytics.interviews_this_month,
                "interviews_today": analytics.interviews_today,
            }
        )
        
        return updated_analytics

    async def update_user_score(self, user_id: uuid.UUID, score: float) -> UserAnalytics:
        """Update user's average score"""
        analytics = await self.get_user_analytics(user_id)
        analytics.update_score(score)
        
        return await self.analytics_repository.update(analytics)

    async def update_streak(self, user_id: uuid.UUID, increment: bool = True) -> UserAnalytics:
        """Update user's streak"""
        analytics = await self.get_user_analytics(user_id)
        
        if increment:
            analytics.increment_streak()
        else:
            analytics.reset_streak()
        
        return await self.analytics_repository.update(analytics)

    async def reset_monthly_counters(self, user_id: uuid.UUID) -> UserAnalytics:
        """Reset user's monthly interview counters (e.g., on subscription upgrade)"""
        analytics = await self.get_user_analytics(user_id)
        analytics.reset_monthly_counters()
        
        return await self.analytics_repository.update(analytics)

    async def get_interviews_remaining(self, user: User) -> int:
        """Get remaining interviews for user based on subscription"""
        analytics = await self.get_user_analytics(user.user_id)
        limits = user.get_session_limits()
        max_interviews = limits.get("interviews_per_month", 0)
        
        if max_interviews == -1:  # Unlimited
            return -1
            
        return analytics.get_remaining_interviews(max_interviews)