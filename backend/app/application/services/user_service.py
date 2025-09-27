"""
User Service - Application Layer
Handles user-related business operations and orchestration
Follows Clean Architecture principles with proper repository abstraction
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from app.domain.entities.user import (
    User,
    UserProfile,
    UserPreferences,
    SubscriptionTier,
)
from app.domain.repositories.user_repository import IUserRepository
from app.application.services.user_analytics_service import UserAnalyticsService
from app.shared.exceptions import (
    BusinessRuleError,
    ResourceNotFoundError,
    ValidationError,
)
from app.shared.logging import get_logger

logger = get_logger(__name__)


class UserService:
    """
    User service following Clean Architecture principles
    Orchestrates user operations and enforces business rules
    """

    def __init__(self, user_repository: IUserRepository, analytics_service: UserAnalyticsService = None):
        self.user_repository = user_repository
        self.analytics_service = analytics_service

    async def get_user_profile(self, user_id: UUID) -> User:
        """Get user profile by ID with proper error handling"""
        logger.info(f"Getting user profile: {user_id}")

        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User not found: {user_id}")

        return user

    async def update_user_profile(
        self, user_id: UUID, profile_data: Dict[str, Any]
    ) -> User:
        """
        Update user profile with business rule validation
        Encapsulates the domain logic and repository interaction
        """
        logger.info(f"Updating profile for user: {user_id}")

        # Get current user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User not found: {user_id}")

        # Validate business rules at service layer
        self._validate_profile_update(profile_data)

        # Apply domain logic (business rules in entity)
        user.update_profile(profile_data)

        # Persist changes through repository
        updated_user = await self.user_repository.update(user)

        logger.info(f"Profile updated successfully for user: {user_id}")
        return updated_user

    async def update_user_preferences(
        self, user_id: UUID, preferences_data: Dict[str, Any]
    ) -> User:
        """
        Update user preferences with validation
        """
        logger.info(f"Updating preferences for user: {user_id}")

        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User not found: {user_id}")

        # Validate preferences at service layer
        self._validate_preferences_update(preferences_data)

        # Apply domain logic
        user.update_preferences(preferences_data)

        # Persist changes
        updated_user = await self.user_repository.update(user)

        logger.info(f"Preferences updated successfully for user: {user_id}")
        return updated_user

    async def upgrade_user_subscription(
        self,
        user_id: UUID,
        tier: SubscriptionTier,
        duration_months: int = 1,
        payment_method_id: Optional[str] = None,
    ) -> User:
        """
        Upgrade user subscription with business validation
        """
        logger.info(f"Upgrading subscription for user: {user_id} to {tier}")

        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User not found: {user_id}")

        # Business rule validation at service layer
        if user.subscription.tier == tier:
            raise BusinessRuleError(f"User already has {tier} subscription")

        # Apply domain logic
        user.upgrade_subscription(tier, duration_months)

        # Persist changes
        updated_user = await self.user_repository.update(user)

        logger.info(f"Subscription upgraded successfully for user: {user_id}")
        return updated_user

    async def start_user_trial(
        self, user_id: UUID, tier: SubscriptionTier, trial_days: int = 14
    ) -> User:
        """
        Start trial subscription with business validation
        """
        logger.info(f"Starting {trial_days}-day trial for user: {user_id}")

        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User not found: {user_id}")

        # Business rule validation
        if user.subscription.is_trial:
            raise BusinessRuleError("User already has an active trial")

        # Apply domain logic
        user.start_trial(tier, trial_days)

        # Persist changes
        updated_user = await self.user_repository.update(user)

        logger.info(f"Trial started successfully for user: {user_id}")
        return updated_user

    async def deactivate_user(
        self, user_id: UUID, reason: Optional[str] = None
    ) -> User:
        """
        Deactivate user account with proper business rules
        """
        logger.info(f"Deactivating user: {user_id}")

        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User not found: {user_id}")

        # Apply domain logic
        user.deactivate(reason)

        # Persist changes
        updated_user = await self.user_repository.update(user)

        logger.info(f"User deactivated successfully: {user_id}")
        return updated_user

    async def mark_user_login(self, user_id: UUID) -> User:
        """
        Mark user login timestamp - used by authentication service
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User not found: {user_id}")

        # Apply domain logic
        user.mark_login()

        # Persist changes
        updated_user = await self.user_repository.update(user)
        return updated_user

    def _validate_profile_update(self, profile_data: Dict[str, Any]) -> None:
        """
        Validate profile update data at service layer
        Business rule validation before domain logic
        """
        if not profile_data:
            raise ValidationError("Profile data cannot be empty")

        # Validate first name
        if "first_name" in profile_data:
            first_name = profile_data["first_name"]
            if first_name is not None and len(str(first_name).strip()) < 2:
                raise ValidationError("First name must be at least 2 characters")

        # Validate phone number format if provided
        if "phone_number" in profile_data and profile_data["phone_number"]:
            phone = str(profile_data["phone_number"])
            if (
                not phone.replace("+", "")
                .replace("-", "")
                .replace(" ", "")
                .replace("(", "")
                .replace(")", "")
                .isdigit()
            ):
                raise ValidationError("Invalid phone number format")

        # Validate years of experience
        if "years_of_experience" in profile_data:
            years = profile_data["years_of_experience"]
            if years is not None and (years < 0 or years > 50):
                raise ValidationError("Years of experience must be between 0 and 50")

    def _validate_preferences_update(self, preferences_data: Dict[str, Any]) -> None:
        """
        Validate preferences update data
        """
        if not preferences_data:
            raise ValidationError("Preferences data cannot be empty")

        # Validate session duration
        if "session_duration_preference" in preferences_data:
            duration = preferences_data["session_duration_preference"]
            if duration and (duration < 15 or duration > 180):
                raise ValidationError(
                    "Session duration must be between 15 and 180 minutes"
                )

        # Validate difficulty level
        if "difficulty_level" in preferences_data:
            difficulty = preferences_data["difficulty_level"]
            valid_levels = ["beginner", "intermediate", "advanced"]
            if difficulty and difficulty not in valid_levels:
                raise ValidationError(
                    f"Difficulty level must be one of: {valid_levels}"
                )

    async def check_interview_creation_limits(self, user_id: UUID) -> tuple[bool, str]:
        """
        Check if user can create a new interview based on subscription limits
        Returns (can_create, reason_if_not)
        """
        logger.info(f"Checking interview limits for user: {user_id}")

        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return False, "User not found"

            # Use analytics service to check limits
            if self.analytics_service:
                can_create, reason = await self.analytics_service.can_create_interview(user)
            else:
                # Fallback to basic subscription check
                limits = user.get_session_limits_for_tier()
                max_interviews = limits.get("interviews_per_month", 0)
                can_create = max_interviews == -1  # Unlimited for premium
                reason = "Premium subscription" if can_create else "Free plan limit reached"

            if not can_create:
                logger.info(f"Interview creation blocked for user {user_id}: {reason}")

            return can_create, reason

        except Exception as e:
            logger.error(
                f"Error checking interview limits for user {user_id}: {str(e)}"
            )
            return False, "Error checking interview limits"

    async def record_interview_creation(self, user_id: UUID) -> None:
        """
        Record that user has started a new interview (increment counters)
        """
        logger.info(f"Recording interview creation for user: {user_id}")

        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise ResourceNotFoundError(f"User not found: {user_id}")

            # Use analytics service to record interview
            if self.analytics_service:
                analytics = await self.analytics_service.record_interview_started(user_id)
                logger.info(
                    f"Interview recorded for user {user_id}. Monthly: {analytics.interviews_this_month}, Daily: {analytics.interviews_today}"
                )
            else:
                logger.warning(f"Analytics service not available for user {user_id}")

        except Exception as e:
            logger.error(
                f"Failed to record interview creation for user {user_id}: {str(e)}"
            )
            raise BusinessRuleError(f"Failed to record interview creation: {str(e)}")

    async def get_user_interview_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get user's interview statistics and limits
        """
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise ResourceNotFoundError(f"User not found: {user_id}")

            # Get analytics data
            analytics = None
            can_create = False
            reason = "Analytics service unavailable"
            remaining_interviews = 0
            
            if self.analytics_service:
                analytics = await self.analytics_service.get_user_analytics(user_id)
                can_create, reason = await self.analytics_service.can_create_interview(user)
                remaining_interviews = await self.analytics_service.get_interviews_remaining(user)
                if remaining_interviews == -1:
                    remaining_interviews = "unlimited"

            return {
                "interviews_this_month": analytics.interviews_this_month if analytics else 0,
                "interviews_today": analytics.interviews_today if analytics else 0,
                "last_interview_date": (
                    analytics.last_interview_date.isoformat()
                    if analytics and analytics.last_interview_date
                    else None
                ),
                "can_create_interview": can_create,
                "limit_reason": reason if not can_create else None,
                "remaining_interviews": remaining_interviews,
                "subscription_tier": user.subscription.tier.value,
                "is_premium": user.subscription.tier != SubscriptionTier.FREE,
                "avg_score": analytics.avg_score if analytics else None,
                "streak": analytics.streak if analytics else 0,
            }

        except Exception as e:
            logger.error(f"Failed to get interview stats for user {user_id}: {str(e)}")
            raise BusinessRuleError(f"Failed to get interview statistics: {str(e)}")
