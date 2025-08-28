"""
Session Application Service
Orchestrates session use cases with repository integration
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from app.domain.entities.session import (
    InterviewSession,
    SessionStatus,
    DifficultyLevel,
    SessionConfig,
    Message,
    MessageRole,
    MessageType,
)
from app.domain.repositories.session_repository import ISessionRepository
from app.domain.repositories.user_repository import IUserRepository
from app.shared.logging import get_logger
from app.shared.exceptions import ResourceNotFoundError, ValidationError, ConflictError

logger = get_logger(__name__)


class SessionService:
    """Application service for session management"""

    def __init__(
        self, session_repository: ISessionRepository, user_repository: IUserRepository
    ):
        self.session_repository = session_repository
        self.user_repository = user_repository

    async def create_session(
        self,
        user_id: UUID,
        topic: str,
        difficulty_level: str,
        session_config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> InterviewSession:
        """Create a new interview session"""
        logger.info(f"Creating new session for user: {user_id}, topic: {topic}")

        # Verify user exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        # Check if user has active session
        active_session = await self.session_repository.get_active_session_for_user(
            user_id
        )
        if active_session:
            raise ConflictError(
                f"User already has an active session: {active_session.session_id}. "
                "Please complete or abandon the current session before starting a new one."
            )

        # Validate topic and difficulty
        if not topic or len(topic.strip()) < 5:
            raise ValidationError("Topic must be at least 5 characters long")

        # Use the DifficultyLevel enum values for validation
        valid_difficulties = [level.value for level in DifficultyLevel]
        if difficulty_level not in valid_difficulties:
            raise ValidationError(
                f"Difficulty must be one of: {', '.join(valid_difficulties)}"
            )

        # Create session configuration
        config = SessionConfig(
            topic=topic,
            difficulty_level=DifficultyLevel(difficulty_level),
            max_duration_minutes=(
                session_config.get("max_duration_minutes", 60) if session_config else 60
            ),
            enable_hints=(
                session_config.get("enable_hints", True) if session_config else True
            ),
            enable_real_time_feedback=(
                session_config.get("enable_real_time_feedback", True)
                if session_config
                else True
            ),
            custom_requirements=(
                session_config.get("custom_requirements") if session_config else None
            ),
        )

        # Create new session
        from uuid import uuid4

        interview_session = InterviewSession(
            session_id=uuid4(),
            user_id=user_id,
            config=config,
        )

        # Add initial system message
        system_message = Message(
            message_id=uuid4(),
            role=MessageRole.SYSTEM,
            content=f"Welcome to your system design interview practice session on '{topic}'. "
            f"This session is set to {difficulty_level.lower()} difficulty. "
            "I'm here to guide you through the problem step by step. Let's begin!",
            message_type=MessageType.TEXT,
        )
        interview_session.messages.append(system_message)

        # Save to repository
        created_session = await self.session_repository.create(interview_session)

        logger.info(f"Session created successfully: {created_session.session_id}")
        return created_session

    async def get_session(self, session_id: UUID) -> InterviewSession:
        """Get session by ID"""
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise ResourceNotFoundError(f"Session {session_id} not found")
        return session

    async def get_user_sessions(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[InterviewSession]:
        """Get all sessions for a user"""
        # Verify user exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        return await self.session_repository.get_by_user_id(user_id, limit, offset)

    async def get_user_active_session(
        self, user_id: UUID
    ) -> Optional[InterviewSession]:
        """Get active session for user"""
        return await self.session_repository.get_active_session_for_user(user_id)

    async def add_message_to_session(
        self,
        session_id: UUID,
        role: str,
        content: str,
        message_type: str = "TEXT",
        metadata: Optional[Dict] = None,
    ) -> Message:
        """Add a message to a session"""
        logger.info(f"Adding message to session: {session_id}, role: {role}")

        # Get session
        session = await self.get_session(session_id)

        if session.status != SessionStatus.ACTIVE:
            raise ValidationError(
                f"Cannot add messages to {session.status.value.lower()} session"
            )

        # Validate role
        try:
            message_role = MessageRole(role.upper())
        except ValueError:
            raise ValidationError(f"Invalid message role: {role}")

        # Create message
        from uuid import uuid4

        message = Message(
            message_id=uuid4(),
            role=message_role,
            content=content,
            message_type=(
                MessageType(message_type) if message_type else MessageType.TEXT
            ),
            metadata=metadata or {},
        )

        # Add to session
        session.messages.append(message)

        # Update session
        await self.session_repository.update(session)

        logger.info(f"Message added to session: {session_id}")
        return message

    async def update_session_status(
        self, session_id: UUID, status: str
    ) -> InterviewSession:
        """Update session status"""
        logger.info(f"Updating session status: {session_id} -> {status}")

        session = await self.get_session(session_id)

        try:
            new_status = SessionStatus(status.upper())
        except ValueError:
            valid_statuses = [s.value for s in SessionStatus]
            raise ValidationError(
                f"Invalid status: {status}. Valid statuses: {', '.join(valid_statuses)}"
            )

        # Update status
        if new_status == SessionStatus.COMPLETED:
            session.status = SessionStatus.COMPLETED
            session.ended_at = datetime.now(timezone.utc)
            session.total_duration = session._calculate_duration()
        elif new_status == SessionStatus.ABANDONED:
            session.status = SessionStatus.ABANDONED
            session.ended_at = datetime.now(timezone.utc)
            session.total_duration = session._calculate_duration()
        else:
            session.status = new_status

        session._mark_as_updated()

        # Save changes
        updated_session = await self.session_repository.update(session)

        logger.info(f"Session status updated: {session_id} -> {status}")
        return updated_session

    async def provide_session_feedback(
        self, session_id: UUID, feedback: Dict[str, Any]
    ) -> InterviewSession:
        """Add feedback to a session"""
        logger.info(f"Adding feedback to session: {session_id}")

        session = await self.get_session(session_id)

        if session.status not in [SessionStatus.COMPLETED, SessionStatus.ABANDONED]:
            raise ValidationError(
                "Feedback can only be provided for completed or abandoned sessions"
            )

        # Add feedback (store in a metadata attribute for now)
        if not hasattr(session, "feedback"):
            session.feedback = feedback
        else:
            session.feedback.update(feedback)

        session._mark_as_updated()

        # Save changes
        updated_session = await self.session_repository.update(session)

        logger.info(f"Feedback added to session: {session_id}")
        return updated_session

    async def get_session_messages(
        self, session_id: UUID, limit: Optional[int] = None, offset: int = 0
    ) -> List[Message]:
        """Get messages for a session"""
        # Verify session exists
        await self.get_session(session_id)

        return await self.session_repository.get_session_messages(
            session_id, limit, offset
        )

    async def get_user_session_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get session statistics for a user"""
        # Verify user exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        return await self.session_repository.get_user_session_stats(user_id)

    async def delete_session(self, session_id: UUID) -> bool:
        """Delete a session (admin only)"""
        logger.warning(f"Deleting session: {session_id}")

        # Verify session exists
        await self.get_session(session_id)

        # Delete session
        result = await self.session_repository.delete(session_id)

        if result:
            logger.warning(f"Session deleted: {session_id}")

        return result

    async def search_sessions_by_topic(
        self, topic_query: str, limit: int = 20, offset: int = 0
    ) -> List[InterviewSession]:
        """Search sessions by topic (simplified - can be enhanced with full-text search)"""
        # This is a basic implementation
        # In production, you might want to implement full-text search
        sessions = await self.session_repository.get_sessions_by_status(
            SessionStatus.COMPLETED, limit * 2, offset  # Get more to filter
        )

        # Simple string matching filter
        filtered_sessions = [
            session
            for session in sessions
            if topic_query.lower() in session.topic.lower()
        ]

        return filtered_sessions[:limit]
