"""
Session Repository Interface
Defines contract for session data persistence
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.session import InterviewSession, SessionStatus


class ISessionRepository(ABC):
    """Session repository interface"""

    @abstractmethod
    async def create(self, session: InterviewSession) -> InterviewSession:
        """Create a new session"""
        pass

    @abstractmethod
    async def get_by_id(self, session_id: UUID) -> Optional[InterviewSession]:
        """Get session by ID"""
        pass

    @abstractmethod
    async def get_by_user_id(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[InterviewSession]:
        """Get sessions for a user"""
        pass

    @abstractmethod
    async def get_active_session_for_user(
        self, user_id: UUID
    ) -> Optional[InterviewSession]:
        """Get active session for a user (if any)"""
        pass

    @abstractmethod
    async def update(self, session: InterviewSession) -> InterviewSession:
        """Update existing session"""
        pass

    @abstractmethod
    async def delete(self, session_id: UUID) -> bool:
        """Delete session (soft delete recommended)"""
        pass

    @abstractmethod
    async def get_sessions_by_status(
        self, status: SessionStatus, limit: int = 50, offset: int = 0
    ) -> List[InterviewSession]:
        """Get sessions by status"""
        pass

    @abstractmethod
    async def get_user_session_stats(self, user_id: UUID) -> dict:
        """Get session statistics for a user"""
        pass
