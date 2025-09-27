"""
User Subscription Repository Interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List
import uuid
from datetime import datetime

from app.domain.entities.subscription import UserSubscription


class UserSubscriptionRepository(ABC):
    """Abstract repository for user subscription operations"""

    @abstractmethod
    async def create_user_subscription(
        self, 
        user_id: uuid.UUID, 
        subscription_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> UserSubscription:
        """Create new user subscription record"""
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[UserSubscription]:
        """Get active user subscription by user ID"""
        pass

    @abstractmethod
    async def get_by_id(self, subscription_id: uuid.UUID) -> Optional[UserSubscription]:
        """Get user subscription by ID"""
        pass

    @abstractmethod
    async def update(self, user_subscription: UserSubscription) -> UserSubscription:
        """Update user subscription record"""
        pass

    @abstractmethod
    async def deactivate(self, user_id: uuid.UUID) -> bool:
        """Deactivate current user subscription"""
        pass

    @abstractmethod
    async def get_user_subscription_with_details(self, user_id: uuid.UUID) -> Optional[dict]:
        """Get user subscription with joined subscription and user details"""
        pass