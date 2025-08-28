"""
PostgreSQL Session Repository Implementation
Handles session persistence with PostgreSQL database
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.session import InterviewSession, SessionStatus, Message
from app.domain.repositories.session_repository import ISessionRepository
from app.infrastructure.database.models.session_model import SessionModel
from app.infrastructure.database.models.message_model import MessageModel
from app.shared.logging import get_logger
from app.shared.exceptions import ResourceNotFoundError

logger = get_logger(__name__)


class PostgreSQLSessionRepository(ISessionRepository):
    """PostgreSQL implementation of session repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, interview_session: InterviewSession) -> InterviewSession:
        """Create a new session"""
        logger.info(f"Creating session: {interview_session.session_id}")

        # Create session model
        session_model = SessionModel.from_entity(interview_session)
        self.session.add(session_model)

        # Create message models for any existing messages
        for message in interview_session.messages:
            message_model = MessageModel.from_entity(
                message, interview_session.session_id
            )
            self.session.add(message_model)

        await self.session.commit()
        await self.session.refresh(session_model)

        logger.info(f"Session created successfully: {interview_session.session_id}")
        return session_model.to_entity()

    async def get_by_id(self, session_id: UUID) -> Optional[InterviewSession]:
        """Get session by ID with messages"""
        stmt = (
            select(SessionModel)
            .options(selectinload(SessionModel.messages))
            .where(SessionModel.id == session_id)
        )
        result = await self.session.execute(stmt)
        session_model = result.scalar_one_or_none()

        if session_model:
            return session_model.to_entity()
        return None

    async def get_by_user_id(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[InterviewSession]:
        """Get sessions for a user"""
        stmt = (
            select(SessionModel)
            .options(selectinload(SessionModel.messages))
            .where(SessionModel.user_id == user_id)
            .order_by(desc(SessionModel.created_at))
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        session_models = result.scalars().all()

        return [model.to_entity() for model in session_models]

    async def get_active_session_for_user(
        self, user_id: UUID
    ) -> Optional[InterviewSession]:
        """Get active session for a user (if any)"""
        stmt = (
            select(SessionModel)
            .options(selectinload(SessionModel.messages))
            .where(
                and_(
                    SessionModel.user_id == user_id,
                    SessionModel.status == SessionStatus.ACTIVE.value,
                )
            )
            .order_by(desc(SessionModel.created_at))
            .limit(1)
        )

        result = await self.session.execute(stmt)
        session_model = result.scalar_one_or_none()

        if session_model:
            return session_model.to_entity()
        return None

    async def update(self, interview_session: InterviewSession) -> InterviewSession:
        """Update existing session"""
        logger.info(f"Updating session: {interview_session.session_id}")

        # Get existing session model
        stmt = select(SessionModel).where(
            SessionModel.id == interview_session.session_id
        )
        result = await self.session.execute(stmt)
        session_model = result.scalar_one_or_none()

        if not session_model:
            raise ResourceNotFoundError(
                f"Session {interview_session.session_id} not found"
            )

        # Update session fields
        session_model.update_from_entity(interview_session)

        # Handle messages - for now, we'll add new messages only
        # In a production system, you might want more sophisticated message handling
        existing_message_ids = {
            msg.id
            for msg in await self.session.execute(
                select(MessageModel.id).where(
                    MessageModel.session_id == interview_session.session_id
                )
            )
        }

        # Add new messages
        for message in interview_session.messages:
            if message.message_id not in existing_message_ids:
                message_model = MessageModel.from_entity(
                    message, interview_session.session_id
                )
                self.session.add(message_model)

        await self.session.commit()
        await self.session.refresh(session_model)

        logger.info(f"Session updated successfully: {interview_session.session_id}")

        # Return updated entity with fresh data
        return await self.get_by_id(interview_session.session_id)

    async def delete(self, session_id: UUID) -> bool:
        """Delete session (hard delete - messages will be cascade deleted)"""
        stmt = select(SessionModel).where(SessionModel.id == session_id)
        result = await self.session.execute(stmt)
        session_model = result.scalar_one_or_none()

        if session_model:
            await self.session.delete(session_model)
            await self.session.commit()
            logger.info(f"Session deleted: {session_id}")
            return True

        return False

    async def get_sessions_by_status(
        self, status: SessionStatus, limit: int = 50, offset: int = 0
    ) -> List[InterviewSession]:
        """Get sessions by status"""
        stmt = (
            select(SessionModel)
            .options(selectinload(SessionModel.messages))
            .where(SessionModel.status == status.value)
            .order_by(desc(SessionModel.created_at))
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        session_models = result.scalars().all()

        return [model.to_entity() for model in session_models]

    async def get_user_session_stats(self, user_id: UUID) -> dict:
        """Get session statistics for a user"""
        # Get basic counts
        total_sessions_stmt = (
            select(func.count())
            .select_from(SessionModel)
            .where(SessionModel.user_id == user_id)
        )
        total_sessions = await self.session.scalar(total_sessions_stmt)

        if total_sessions == 0:
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

        # Get sessions by status
        completed_sessions_stmt = (
            select(func.count())
            .select_from(SessionModel)
            .where(
                and_(
                    SessionModel.user_id == user_id,
                    SessionModel.status == SessionStatus.COMPLETED.value,
                )
            )
        )
        completed_sessions = await self.session.scalar(completed_sessions_stmt)

        abandoned_sessions_stmt = (
            select(func.count())
            .select_from(SessionModel)
            .where(
                and_(
                    SessionModel.user_id == user_id,
                    SessionModel.status == SessionStatus.ABANDONED.value,
                )
            )
        )
        abandoned_sessions = await self.session.scalar(abandoned_sessions_stmt)

        active_sessions_stmt = (
            select(func.count())
            .select_from(SessionModel)
            .where(
                and_(
                    SessionModel.user_id == user_id,
                    SessionModel.status == SessionStatus.ACTIVE.value,
                )
            )
        )
        active_sessions = await self.session.scalar(active_sessions_stmt)

        # Get total time spent (sum of total_duration where not null)
        total_time_stmt = select(
            func.coalesce(func.sum(SessionModel.total_duration), 0)
        ).where(SessionModel.user_id == user_id)
        total_time_spent = await self.session.scalar(total_time_stmt)

        # Calculate average duration
        avg_duration_minutes = (
            (total_time_spent / 60) / total_sessions if total_sessions > 0 else 0
        )

        # Get all user sessions for detailed analysis
        user_sessions_stmt = select(
            SessionModel.topic, SessionModel.difficulty_level, SessionModel.created_at
        ).where(SessionModel.user_id == user_id)
        result = await self.session.execute(user_sessions_stmt)
        user_sessions = result.all()

        # Topic analysis
        topic_counts = {}
        for session in user_sessions:
            topic = session.topic
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        favorite_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        favorite_topics = [topic for topic, _ in favorite_topics[:5]]  # Top 5

        # Difficulty breakdown
        difficulty_breakdown = {}
        for session in user_sessions:
            diff = session.difficulty_level
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
            "total_time_spent": int(total_time_spent),
            "average_session_duration": avg_duration_minutes,
            "favorite_topics": favorite_topics,
            "difficulty_breakdown": difficulty_breakdown,
            "monthly_activity": monthly_activity,
        }

    async def add_message_to_session(
        self, session_id: UUID, message: Message
    ) -> Message:
        """Add a message to an existing session"""
        logger.info(f"Adding message to session: {session_id}")

        # Verify session exists
        session_exists_stmt = select(SessionModel.id).where(
            SessionModel.id == session_id
        )
        session_exists = await self.session.scalar(session_exists_stmt)

        if not session_exists:
            raise ResourceNotFoundError(f"Session {session_id} not found")

        # Create and save message
        message_model = MessageModel.from_entity(message, session_id)
        self.session.add(message_model)

        await self.session.commit()
        await self.session.refresh(message_model)

        return message_model.to_entity()

    async def get_session_messages(
        self, session_id: UUID, limit: Optional[int] = None, offset: int = 0
    ) -> List[Message]:
        """Get messages for a specific session"""
        stmt = (
            select(MessageModel)
            .where(MessageModel.session_id == session_id)
            .order_by(MessageModel.timestamp)
            .offset(offset)
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        message_models = result.scalars().all()

        return [model.to_entity() for model in message_models]
