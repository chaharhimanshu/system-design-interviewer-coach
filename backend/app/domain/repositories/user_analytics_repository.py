"""
User Analytics Repository Interface
"""

from abc import ABC, abstractmethod
from typing import Optional
import uuid

from app.domain.entities.user_analytics import UserAnalytics


class UserAnalyticsRepository(ABC):
    """Abstract repository for user analytics operations"""

    @abstractmethod
    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[UserAnalytics]:
        """Get user analytics by user ID"""
        pass

    @abstractmethod
    async def create(self, analytics: UserAnalytics) -> UserAnalytics:
        """Create new user analytics record"""
        pass

    @abstractmethod
    async def update(self, analytics: UserAnalytics) -> UserAnalytics:
        """Update user analytics record"""
        pass

    @abstractmethod
    async def get_or_create(self, user_id: uuid.UUID) -> UserAnalytics:
        """Get existing analytics or create new one for user"""
        pass

    @abstractmethod
    async def delete(self, user_id: uuid.UUID) -> bool:
        """Delete user analytics record"""
        pass