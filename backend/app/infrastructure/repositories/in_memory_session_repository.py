"""
In-Memory Session Repository Implementation
Temporary implementation for MVP development
TODO: Replace with PostgreSQL implementation
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from app.domain.entities.session import InterviewSession, SessionStatus
from app.domain.repositories.session_repository import ISessionRepository
from app.shared.logging import get_logger

logger = get_logger(__name__)


class InMemorySessionRepository(ISessionRepository):
    """In-memory session repository for MVP development"""

    def __init__(self):
        self._sessions: Dict[UUID, InterviewSession] = {}
        self._user_sessions: Dict[UUID, List[UUID]] = {}

    async def create(self, session: InterviewSession) -> InterviewSession:
        """Create a new session"""
        logger.info(f"Creating session: {session.session_id}")

        self._sessions[session.session_id] = session

        # Add to user sessions index
        if session.user_id not in self._user_sessions:
            self._user_sessions[session.user_id] = []
        self._user_sessions[session.user_id].append(session.session_id)

        return session

    async def get_by_id(self, session_id: UUID) -> Optional[InterviewSession]:
        """Get session by ID"""
        return self._sessions.get(session_id)

    async def get_by_user_id(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[InterviewSession]:
        """Get sessions for a user"""
        user_session_ids = self._user_sessions.get(user_id, [])

        # Sort by creation time (newest first)
        sessions = [
            self._sessions[sid] for sid in user_session_ids if sid in self._sessions
        ]
        sessions.sort(key=lambda s: s.created_at, reverse=True)

        # Apply pagination
        return sessions[offset : offset + limit]

    async def get_active_session_for_user(
        self, user_id: UUID
    ) -> Optional[InterviewSession]:
        """Get active session for a user (if any)"""
        user_session_ids = self._user_sessions.get(user_id, [])

        for session_id in user_session_ids:
            session = self._sessions.get(session_id)
            if session and session.status == SessionStatus.ACTIVE:
                return session

        return None

    async def update(self, session: InterviewSession) -> InterviewSession:
        """Update existing session"""
        if session.session_id not in self._sessions:
            raise ValueError(f"Session {session.session_id} not found")

        logger.info(f"Updating session: {session.session_id}")
        self._sessions[session.session_id] = session
        return session

    async def delete(self, session_id: UUID) -> bool:
        """Delete session (soft delete recommended)"""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            # Remove from user sessions index
            if session.user_id in self._user_sessions:
                try:
                    self._user_sessions[session.user_id].remove(session_id)
                except ValueError:
                    pass

            del self._sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False

    async def get_sessions_by_status(
        self, status: SessionStatus, limit: int = 50, offset: int = 0
    ) -> List[InterviewSession]:
        """Get sessions by status"""
        matching_sessions = [
            session for session in self._sessions.values() if session.status == status
        ]

        # Sort by creation time (newest first)
        matching_sessions.sort(key=lambda s: s.created_at, reverse=True)

        # Apply pagination
        return matching_sessions[offset : offset + limit]

    async def get_user_session_stats(self, user_id: UUID) -> dict:
        """Get session statistics for a user"""
        user_session_ids = self._user_sessions.get(user_id, [])
        user_sessions = [
            self._sessions[sid] for sid in user_session_ids if sid in self._sessions
        ]

        if not user_sessions:
            return {
                "user_id": user_id,
                "total_sessions": 0,
                "completed_sessions": 0,
                "abandoned_sessions": 0,
                "active_sessions": 0,
                "total_time_spent": 0,
                "average_session_duration": 0.0,
                "favorite_topics": [],
                "difficulty_breakdown": {},
                "monthly_activity": {},
            }

        # Calculate stats
        total_sessions = len(user_sessions)
        completed_sessions = sum(
            1 for s in user_sessions if s.status == SessionStatus.COMPLETED
        )
        abandoned_sessions = sum(
            1 for s in user_sessions if s.status == SessionStatus.ABANDONED
        )
        active_sessions = sum(
            1 for s in user_sessions if s.status == SessionStatus.ACTIVE
        )

        # Calculate total time spent (in seconds)
        total_time_spent = 0
        for session in user_sessions:
            if session.total_duration:
                total_time_spent += session.total_duration
            elif session.status == SessionStatus.ACTIVE:
                # For active sessions, calculate current duration
                duration = (
                    datetime.now(timezone.utc) - session.started_at
                ).total_seconds()
                total_time_spent += int(duration)

        # Average session duration in minutes
        avg_duration_minutes = (
            (total_time_spent / 60) / total_sessions if total_sessions > 0 else 0
        )

        # Topic analysis
        topic_counts = {}
        for session in user_sessions:
            topic = session.config.topic
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        favorite_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        favorite_topics = [topic for topic, _ in favorite_topics[:5]]  # Top 5

        # Difficulty breakdown
        difficulty_breakdown = {}
        for session in user_sessions:
            diff = session.config.difficulty_level.value
            difficulty_breakdown[diff] = difficulty_breakdown.get(diff, 0) + 1

        # Monthly activity (simplified - just current month)
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        monthly_activity = {current_month: total_sessions}

        return {
            "user_id": user_id,
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "abandoned_sessions": abandoned_sessions,
            "active_sessions": active_sessions,
            "total_time_spent": total_time_spent,
            "average_session_duration": avg_duration_minutes,
            "favorite_topics": favorite_topics,
            "difficulty_breakdown": difficulty_breakdown,
            "monthly_activity": monthly_activity,
        }

    # Helper methods for development
    def get_all_sessions(self) -> List[InterviewSession]:
        """Get all sessions (for debugging)"""
        return list(self._sessions.values())

    def clear_all_sessions(self) -> None:
        """Clear all sessions (for testing)"""
        self._sessions.clear()
        self._user_sessions.clear()
        logger.warning("All sessions cleared from in-memory repository")

    def get_session_count(self) -> int:
        """Get total session count"""
        return len(self._sessions)
