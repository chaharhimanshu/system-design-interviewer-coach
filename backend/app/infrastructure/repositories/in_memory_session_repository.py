"""
In-Memory Session Repository Implementation
Simple implementation for MVP testing
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

from app.domain.entities.session import InterviewSession, SessionStatus, Message
from app.domain.repositories.session_repository import ISessionRepository


class InMemorySessionRepository(ISessionRepository):
    """In-memory implementation of session repository"""

    def __init__(self):
        self.sessions: Dict[UUID, InterviewSession] = {}
        self.messages: Dict[UUID, List[Message]] = {}

    async def create(self, session: InterviewSession) -> InterviewSession:
        """Create a new session"""
        self.sessions[session.session_id] = session
        self.messages[session.session_id] = session.messages.copy()
        return session

    async def get_by_id(self, session_id: UUID) -> Optional[InterviewSession]:
        """Get session by ID"""
        return self.sessions.get(session_id)

    async def get_by_user_id(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[InterviewSession]:
        """Get sessions for a user"""
        user_sessions = [
            session for session in self.sessions.values() if session.user_id == user_id
        ]
        return user_sessions[offset : offset + limit]

    async def get_active_session_for_user(
        self, user_id: UUID
    ) -> Optional[InterviewSession]:
        """Get active session for a user (if any)"""
        for session in self.sessions.values():
            if session.user_id == user_id and session.status == SessionStatus.ACTIVE:
                return session
        return None

    async def update(self, session: InterviewSession) -> InterviewSession:
        """Update existing session"""
        self.sessions[session.session_id] = session
        self.messages[session.session_id] = session.messages.copy()
        return session

    async def delete(self, session_id: UUID) -> bool:
        """Delete session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            if session_id in self.messages:
                del self.messages[session_id]
            return True
        return False

    async def get_sessions_by_status(
        self, status: SessionStatus, limit: int = 50, offset: int = 0
    ) -> List[InterviewSession]:
        """Get sessions by status"""
        status_sessions = [
            session for session in self.sessions.values() if session.status == status
        ]
        return status_sessions[offset : offset + limit]

    async def get_user_session_stats(self, user_id: UUID) -> dict:
        """Get session statistics for a user"""
        user_sessions = [
            session for session in self.sessions.values() if session.user_id == user_id
        ]

        total_sessions = len(user_sessions)
        completed_sessions = len(
            [s for s in user_sessions if s.status == SessionStatus.COMPLETED]
        )
        abandoned_sessions = len(
            [s for s in user_sessions if s.status == SessionStatus.ABANDONED]
        )
        active_sessions = len(
            [s for s in user_sessions if s.status == SessionStatus.ACTIVE]
        )

        return {
            "user_id": user_id,
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "abandoned_sessions": abandoned_sessions,
            "active_sessions": active_sessions,
            "total_time_spent": 0,
            "average_session_duration": 0.0,
            "favorite_topics": [],
            "difficulty_breakdown": {},
            "monthly_activity": {},
        }

    async def add_message_to_session(
        self, session_id: UUID, message: Message
    ) -> Message:
        """Add a message to an existing session"""
        if session_id in self.sessions:
            self.sessions[session_id].messages.append(message)
            if session_id not in self.messages:
                self.messages[session_id] = []
            self.messages[session_id].append(message)
        return message

    async def get_session_messages(
        self, session_id: UUID, limit: Optional[int] = None, offset: int = 0
    ) -> List[Message]:
        """Get messages for a specific session"""
        session_messages = self.messages.get(session_id, [])
        if limit:
            return session_messages[offset : offset + limit]
        return session_messages[offset:]

    async def update_session_status(
        self, session_id: UUID, status: SessionStatus
    ) -> bool:
        """Update session status"""
        if session_id in self.sessions:
            self.sessions[session_id].status = status
            return True
        return False
