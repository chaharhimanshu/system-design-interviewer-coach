"""
SQLAlchemy implementation of UserSubscription Repository
"""

from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.exc import SQLAlchemyError

from app.domain.repositories.user_subscription_repository import UserSubscriptionRepository
from app.domain.entities.subscription import UserSubscription, SubscriptionStatus
from app.infrastructure.database.models.subscription_model import (
    UserSubscriptionModel, 
    SubscriptionModel
)
from app.infrastructure.database.models.user_model import UserModel
from app.shared.exceptions import (
    DatabaseError,
    ResourceNotFoundError,
)
from app.shared.logging import get_logger

logger = get_logger(__name__)


class SQLAlchemyUserSubscriptionRepository(UserSubscriptionRepository):
    """SQLAlchemy implementation of user subscription repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _model_to_entity(self, model: UserSubscriptionModel) -> UserSubscription:
        """Convert database model to domain entity"""
        return UserSubscription(
            id=model.id,
            user_id=model.user_id,
            subscription_id=model.subscription_id,
            status=SubscriptionStatus(model.status),
            start_date=model.start_date,
            end_date=model.end_date,
            created_at=getattr(model, 'created_at', None),
            updated_at=getattr(model, 'updated_at', None)
        )

    async def create_user_subscription(
        self, 
        user_id: uuid.UUID, 
        subscription_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> UserSubscription:
        """Create new user subscription record"""
        try:
            # Create the database model
            user_subscription_model = UserSubscriptionModel(
                user_id=user_id,
                subscription_id=subscription_id,
                start_date=start_date or datetime.now(timezone.utc),
                end_date=end_date,
                status="active"
            )
            
            self.session.add(user_subscription_model)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(user_subscription_model)
            
            # Convert to domain entity
            user_subscription = self._model_to_entity(user_subscription_model)
            
            logger.info(f"User subscription created: {user_subscription.id}")
            return user_subscription

        except SQLAlchemyError as e:
            logger.error(f"Database error creating user subscription: {e}")
            raise DatabaseError(f"Failed to create user subscription: {e}")

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[UserSubscription]:
        """Get active user subscription by user ID"""
        try:
            stmt = (
                select(UserSubscriptionModel)
                .where(
                    and_(
                        UserSubscriptionModel.user_id == user_id,
                        UserSubscriptionModel.status == "active"
                    )
                )
                .options(selectinload(UserSubscriptionModel.subscription))
                .order_by(UserSubscriptionModel.start_date.desc())
            )
            
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            return self._model_to_entity(model) if model else None

        except SQLAlchemyError as e:
            logger.error(f"Database error getting user subscription: {e}")
            raise DatabaseError(f"Failed to get user subscription: {e}")

    async def get_by_id(self, subscription_id: uuid.UUID) -> Optional[UserSubscription]:
        """Get user subscription by ID"""
        try:
            stmt = (
                select(UserSubscriptionModel)
                .where(UserSubscriptionModel.id == subscription_id)
                .options(
                    selectinload(UserSubscriptionModel.subscription),
                    selectinload(UserSubscriptionModel.user)
                )
            )
            
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            return self._model_to_entity(model) if model else None

        except SQLAlchemyError as e:
            logger.error(f"Database error getting user subscription by ID: {e}")
            raise DatabaseError(f"Failed to get user subscription: {e}")

    async def update(self, user_subscription: UserSubscription) -> UserSubscription:
        """Update user subscription record"""
        try:
            # First get the existing model
            stmt = select(UserSubscriptionModel).where(UserSubscriptionModel.id == user_subscription.id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                raise ResourceNotFoundError(f"User subscription not found: {user_subscription.id}")
            
            # Update model fields
            model.status = user_subscription.status.value
            model.start_date = user_subscription.start_date
            model.end_date = user_subscription.end_date
            model.updated_at = datetime.now(timezone.utc)
            
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(model)
            
            # Convert back to domain entity
            updated_entity = self._model_to_entity(model)
            
            logger.info(f"User subscription updated: {user_subscription.id}")
            return updated_entity

        except SQLAlchemyError as e:
            logger.error(f"Database error updating user subscription: {e}")
            raise DatabaseError(f"Failed to update user subscription: {e}")

    async def deactivate(self, user_id: uuid.UUID) -> bool:
        """Deactivate current user subscription"""
        try:
            stmt = (
                update(UserSubscriptionModel)
                .where(
                    and_(
                        UserSubscriptionModel.user_id == user_id,
                        UserSubscriptionModel.status == "active"
                    )
                )
                .values(
                    status="inactive",
                    end_date=datetime.now(timezone.utc)
                )
            )
            
            result = await self.session.execute(stmt)
            await self.session.flush()
            await self.session.commit()
            
            updated_count = result.rowcount
            if updated_count > 0:
                logger.info(f"Deactivated {updated_count} user subscriptions for user {user_id}")
                return True
            
            return False

        except SQLAlchemyError as e:
            logger.error(f"Database error deactivating user subscription: {e}")
            raise DatabaseError(f"Failed to deactivate user subscription: {e}")

    async def get_user_subscription_with_details(self, user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Get user subscription with joined subscription and user details
        This is the common function for fetching comprehensive subscription data
        """
        try:
            # Join user_subscriptions, subscriptions, and users tables
            stmt = (
                select(
                    UserSubscriptionModel,
                    SubscriptionModel,
                    UserModel
                )
                .join(SubscriptionModel, UserSubscriptionModel.subscription_id == SubscriptionModel.id)
                .join(UserModel, UserSubscriptionModel.user_id == UserModel.id)
                .where(
                    and_(
                        UserSubscriptionModel.user_id == user_id,
                        UserSubscriptionModel.status == "active"
                    )
                )
                .order_by(UserSubscriptionModel.start_date.desc())
            )
            
            result = await self.session.execute(stmt)
            row = result.first()
            
            if not row:
                return None
            
            user_sub, subscription, user = row
            
            # Build comprehensive subscription details
            return {
                # User subscription details  
                "user_subscription_id": user_sub.id,
                "user_subscription_start_date": user_sub.start_date,
                "user_subscription_end_date": user_sub.end_date,
                "user_subscription_status": user_sub.status,
                
                # Subscription plan details
                "subscription_id": subscription.id,
                "subscription_name": subscription.tier,  # Using tier as name
                "subscription_tier": subscription.tier,
                "subscription_price": float(subscription.pricing),
                "subscription_billing_cycle": self._get_billing_cycle_by_tier(subscription.tier),
                "subscription_interview_limit": self._get_interview_limit_by_tier(subscription.tier),
                "subscription_details": subscription.details,
                
                # User details
                "user_id": user.id,
                "user_email": user.email,
                "user_name": f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email,
                "user_created_at": user.created_at,
                "user_status": user.status,
                
                # Computed fields
                "is_active": (
                    user_sub.status == "active" and 
                    (user_sub.end_date is None or user_sub.end_date > datetime.now(timezone.utc))
                ),
                "days_remaining": (
                    (user_sub.end_date - datetime.now(timezone.utc)).days
                    if user_sub.end_date and user_sub.end_date > datetime.now(timezone.utc)
                    else None
                )
            }

        except SQLAlchemyError as e:
            logger.error(f"Database error getting user subscription details: {e}")
            raise DatabaseError(f"Failed to get user subscription details: {e}")

    def _get_interview_limit_by_tier(self, tier: str) -> int:
        """Get interview limit based on subscription tier"""
        tier_limits = {
            "free": 5,
            "premium": 50,
            "enterprise": -1  # Unlimited
        }
        return tier_limits.get(tier.lower(), 5)  # Default to free tier limit

    def _get_billing_cycle_by_tier(self, tier: str) -> str:
        """Get billing cycle based on subscription tier"""
        return "monthly"  # Default billing cycle for all tiers