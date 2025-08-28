"""
User Repository Interface - Domain Layer
Defines the contract for user data access
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from app.domain.entities.user import User


class IUserRepository(ABC):
    """User repository interface following Repository pattern"""

    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user"""
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass

    @abstractmethod
    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        """Get user by Google ID"""
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        """Update existing user"""
        pass

    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """Delete user (soft delete)"""
        pass

    @abstractmethod
    async def list_users(
        self,
        offset: int = 0,
        limit: int = 10,
        status: Optional[str] = None,
        subscription_tier: Optional[str] = None,
    ) -> List[User]:
        """List users with pagination and filters"""
        pass

    @abstractmethod
    async def count_users(
        self, status: Optional[str] = None, subscription_tier: Optional[str] = None
    ) -> int:
        """Count users with filters"""
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email"""
        pass

    @abstractmethod
    async def get_active_users(self) -> List[User]:
        """Get all active users"""
        pass
