"""
In-Memory User Repository Implementation
Simple implementation for MVP testing
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

from app.domain.entities.user import User, UserStatus
from app.domain.repositories.user_repository import IUserRepository


class InMemoryUserRepository(IUserRepository):
    """In-memory implementation of user repository"""

    def __init__(self):
        self.users: Dict[UUID, User] = {}
        self.email_index: Dict[str, UUID] = {}
        self.google_id_index: Dict[str, UUID] = {}

    async def create(self, user: User) -> User:
        """Create a new user"""
        self.users[user.user_id] = user
        self.email_index[user.email] = user.user_id
        if user.google_id:
            self.google_id_index[user.google_id] = user.user_id
        return user

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        user_id = self.email_index.get(email)
        if user_id:
            return self.users.get(user_id)
        return None

    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        """Get user by Google ID"""
        user_id = self.google_id_index.get(google_id)
        if user_id:
            return self.users.get(user_id)
        return None

    async def update(self, user: User) -> User:
        """Update existing user"""
        self.users[user.user_id] = user
        self.email_index[user.email] = user.user_id
        if user.google_id:
            self.google_id_index[user.google_id] = user.user_id
        return user

    async def delete(self, user_id: UUID) -> bool:
        """Delete user"""
        if user_id in self.users:
            user = self.users[user_id]
            del self.users[user_id]
            del self.email_index[user.email]
            if user.google_id and user.google_id in self.google_id_index:
                del self.google_id_index[user.google_id]
            return True
        return False

    async def list_users(
        self,
        offset: int = 0,
        limit: int = 10,
        status_filter: Optional[UserStatus] = None,
    ) -> List[User]:
        """List users with pagination and optional status filter"""
        users = list(self.users.values())
        if status_filter:
            users = [user for user in users if user.status == status_filter]
        return users[offset : offset + limit]

    async def count_users(self, status_filter: Optional[UserStatus] = None) -> int:
        """Count total users with optional status filter"""
        if status_filter:
            return len(
                [user for user in self.users.values() if user.status == status_filter]
            )
        return len(self.users)

    async def search_users(
        self, search_term: str, limit: int = 10, offset: int = 0
    ) -> List[User]:
        """Search users by name or email"""
        search_term = search_term.lower()
        matching_users = [
            user
            for user in self.users.values()
            if search_term in user.full_name.lower()
            or search_term in user.email.lower()
        ]
        return matching_users[offset : offset + limit]
