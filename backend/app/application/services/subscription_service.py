"""
Subscription Service - Application Layer
Handles subscription-related business operations
"""

from typing import Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timezone

from app.domain.entities.user import User, SubscriptionTier
from app.domain.entities.user_analytics import UserAnalytics
from app.domain.entities.subscription import SubscriptionStatus
from app.domain.repositories.user_repository import IUserRepository
from app.domain.repositories.user_subscription_repository import UserSubscriptionRepository
from app.application.services.user_analytics_service import UserAnalyticsService
from app.shared.exceptions import (
    BusinessRuleError,
    ResourceNotFoundError,
    ValidationError,
)
from app.shared.logging import get_logger

logger = get_logger(__name__)


class SubscriptionService:
    """Service for managing user subscriptions and checking limits"""

    def __init__(
        self, 
        user_repository: IUserRepository,
        user_subscription_repository: UserSubscriptionRepository,
        analytics_service: UserAnalyticsService
    ):
        self.user_repository = user_repository
        self.user_subscription_repository = user_subscription_repository
        self.analytics_service = analytics_service

    async def create_user_subscription(
        self, 
        user_id: UUID, 
        subscription_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create a new user subscription entry or update existing one
        Prevents duplicate entries by updating existing subscription if one exists
        """
        logger.info(f"Creating/updating subscription for user {user_id} with subscription {subscription_id}")

        try:
            # Validate user exists
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise ResourceNotFoundError(f"User not found: {user_id}")

            # Check if user already has an active subscription
            existing_subscription = await self.user_subscription_repository.get_by_user_id(user_id)
            
            if existing_subscription:
                # Update existing subscription instead of creating duplicate
                logger.info(f"Found existing subscription for user {user_id}, updating instead of creating new")
                
                # Update the existing subscription with new values
                existing_subscription.subscription_id = subscription_id
                existing_subscription.start_date = start_date or existing_subscription.start_date
                existing_subscription.end_date = end_date
                # Keep status as active since we're updating to a new subscription
                existing_subscription.status = SubscriptionStatus.ACTIVE
                
                user_subscription = await self.user_subscription_repository.update(existing_subscription)
                action = "updated"
                
            else:
                # Create new subscription since none exists
                logger.info(f"No existing subscription found for user {user_id}, creating new")
                
                user_subscription = await self.user_subscription_repository.create_user_subscription(
                    user_id=user_id,
                    subscription_id=subscription_id,
                    start_date=start_date,
                    end_date=end_date
                )
                action = "created"
            
            # Reset analytics counters for subscription upgrade/creation
            await self.analytics_service.reset_monthly_counters(user_id)
            
            logger.info(f"User subscription {action} successfully for user {user_id}")
            
            return {
                "success": True,
                "action": action,  # "created" or "updated"
                "user_id": str(user_subscription.user_id),
                "subscription_id": str(user_subscription.subscription_id),
                "start_date": user_subscription.start_date.isoformat(),
                "end_date": user_subscription.end_date.isoformat() if user_subscription.end_date else None,
                "status": user_subscription.status.value
            }

        except Exception as e:
            logger.error(f"Failed to create/update user subscription: {str(e)}")
            raise BusinessRuleError(f"Failed to create/update subscription: {str(e)}")

    async def get_user_subscription_details(self, user_id: UUID) -> Dict[str, Any]:
        """
        Common function to fetch user data with subscription and analytics details
        by joining user/subscription/user_subscription tables
        """
        logger.info(f"Fetching subscription details for user {user_id}")

        try:
            # Get user data with subscription details using repository join
            user_subscription_details = await self.user_subscription_repository.get_user_subscription_with_details(user_id)
            
            if not user_subscription_details:
                # User exists but has no subscription (free tier)
                user = await self.user_repository.get_by_id(user_id)
                if not user:
                    raise ResourceNotFoundError(f"User not found: {user_id}")
                
                # Get user analytics
                analytics = await self.analytics_service.get_user_analytics(user_id)
                
                # Free tier limits
                max_interviews = 5
                used_this_month = analytics.interviews_this_month
                remaining = max_interviews - used_this_month
                can_create = remaining > 0
                
                return {
                    # User info (flattened)
                    "user_id": str(user.id),
                    "email": user.email,
                    "user_status": "active",
                    
                    # Subscription info (flattened)
                    "subscription_tier": "free",
                    "subscription_active": True,
                    "subscription_expires_at": None,
                    "is_trial": False,
                    "auto_renew": False,
                    
                    # Interview limits and usage (flattened)
                    "max_interviews_per_month": max_interviews,
                    "interviews_used_this_month": used_this_month,
                    "interviews_used_today": analytics.interviews_today,
                    "remaining_interviews": remaining,
                    "can_create_interview": can_create,
                    "limit_reason": None if can_create else "Free tier monthly limit reached",
                    
                    # Analytics (flattened)
                    "avg_score": analytics.avg_score,
                    "current_streak": analytics.streak,
                    "last_interview_date": analytics.last_interview_date.isoformat() if analytics.last_interview_date else None,
                    
                    # Metadata
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }

            # User has an active subscription
            analytics = await self.analytics_service.get_user_analytics(user_id)
            
            # Calculate interview limits and availability
            max_interviews = user_subscription_details["subscription_interview_limit"] or 999999  # Unlimited = large number
            used_this_month = analytics.interviews_this_month
            remaining = max_interviews - used_this_month if max_interviews != 999999 else "unlimited"
            can_create = remaining == "unlimited" or remaining > 0
            
            result = {
                # User info (flattened)
                "user_id": str(user_subscription_details["user_id"]),
                "email": user_subscription_details["user_email"],
                "user_status": "active",  # Assuming active since they have a subscription
                
                # Subscription info (flattened)
                "subscription_tier": user_subscription_details["subscription_name"],
                "subscription_active": user_subscription_details["user_subscription_status"] == "active",
                "subscription_expires_at": user_subscription_details["user_subscription_end_date"].isoformat() if user_subscription_details["user_subscription_end_date"] else None,
                "is_trial": False,  # TODO: Add trial logic if needed
                "auto_renew": True,  # TODO: Add auto-renew logic if needed
                
                # Interview limits and usage (flattened)
                "max_interviews_per_month": max_interviews,
                "interviews_used_this_month": used_this_month,
                "interviews_used_today": analytics.interviews_today,
                "remaining_interviews": remaining,
                "can_create_interview": can_create,
                "limit_reason": None if can_create else "Monthly limit reached",
                
                # Analytics (flattened)
                "avg_score": analytics.avg_score,
                "current_streak": analytics.streak,
                "last_interview_date": analytics.last_interview_date.isoformat() if analytics.last_interview_date else None,
                
                # Metadata
                "last_updated": datetime.now(timezone.utc).isoformat()
            }

            logger.info(f"Successfully fetched subscription details for user {user_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch user subscription details: {str(e)}")
            raise BusinessRuleError(f"Failed to fetch subscription details: {str(e)}")

    async def check_interview_permissions(self, user_id: UUID) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Quick permission check for interview creation
        Returns: (can_create, reason, subscription_summary)
        """
        try:
            subscription_details = await self.get_user_subscription_details(user_id)
            
            can_create = subscription_details["can_create_interview"]
            reason = subscription_details.get("limit_reason", "")
            
            summary = {
                "tier": subscription_details["subscription_tier"],
                "remaining": subscription_details["remaining_interviews"],
                "used_this_month": subscription_details["interviews_used_this_month"]
            }
            
            return can_create, reason, summary
            
        except Exception as e:
            logger.error(f"Failed to check interview permissions for user {user_id}: {str(e)}")
            return False, f"Permission check failed: {str(e)}", {}

    async def upgrade_user_subscription(
        self, 
        user_id: UUID, 
        new_subscription_id: UUID,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upgrade user to a new subscription tier
        """
        logger.info(f"Upgrading subscription for user {user_id} to subscription {new_subscription_id}")

        try:
            # This would typically:
            # 1. Validate the new subscription
            # 2. End the current subscription
            # 3. Create new subscription record
            # 4. Update user's subscription details
            # 5. Reset analytics counters
            
            # For now, just reset counters on upgrade
            await self.analytics_service.reset_monthly_counters(user_id)
            
            logger.info(f"User subscription upgraded successfully for user {user_id}")
            
            return {
                "success": True,
                "user_id": str(user_id),
                "new_subscription_id": str(new_subscription_id),
                "upgraded_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to upgrade user subscription: {str(e)}")
            raise BusinessRuleError(f"Failed to upgrade subscription: {str(e)}")