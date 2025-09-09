"""
Streaming Service
Business logic for SSE-based real-time communication
"""

from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import Request, HTTPException, status

from app.shared.logging import get_logger
from app.domain.entities.session import InterviewSession
from app.domain.entities.user import User
from app.infrastructure.streaming.sse_manager import get_sse_manager
from app.infrastructure.streaming.session_stream_handler import (
    get_session_stream_handler,
)
from app.infrastructure.streaming.ai_response_streamer import get_ai_response_streamer

logger = get_logger(__name__)


class StreamingService:
    """Service for managing SSE streaming functionality"""

    def __init__(self):
        self.sse_manager = None
        self.session_handler = None
        self.ai_streamer = None

    async def initialize(self):
        """Initialize streaming components"""
        self.sse_manager = await get_sse_manager()
        self.session_handler = await get_session_stream_handler()
        self.ai_streamer = await get_ai_response_streamer()

    async def create_session_stream(
        self, session: InterviewSession, user: User, request: Request
    ):
        """
        Create SSE stream for a session

        Args:
            session: Interview session entity
            user: User entity
            request: FastAPI request object

        Returns:
            StreamingResponse for SSE connection
        """
        # Verify user has access to session
        if session.user_id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session",
            )

        # Verify session is in valid state for streaming
        if session.status not in ["ACTIVE", "PAUSED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session must be active or paused for streaming. Current status: {session.status}",
            )

        logger.info(
            f"Creating SSE stream for session {session.session_id}, user {user.user_id}"
        )

        # Create the SSE connection stream
        response = await self.sse_manager.create_connection_stream(
            session_id=str(session.session_id),
            user_id=str(user.user_id),
            request=request,
        )

        # Send initial session state
        await self.session_handler.send_session_status_update(
            session_id=str(session.session_id),
            status=session.status,
            details={
                "session_name": session.session_name,
                "total_messages": len(session.messages),
                "current_difficulty": session.current_difficulty_level,
                "created_at": (
                    session.created_at.isoformat() if session.created_at else None
                ),
                "last_activity": (
                    session.last_activity_at.isoformat()
                    if session.last_activity_at
                    else None
                ),
            },
        )

        return response

    async def get_session_stream_info(self, session_id: UUID) -> Dict[str, Any]:
        """
        Get information about session streaming status

        Args:
            session_id: Session ID

        Returns:
            Dictionary with stream information
        """
        stats = await self.session_handler.get_session_stream_stats(str(session_id))
        connections = await self.sse_manager.get_session_connections(str(session_id))

        return {
            "session_id": str(session_id),
            "streaming_active": len(connections) > 0,
            "active_connections": len(connections),
            "connection_details": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def send_session_notification(
        self,
        session_id: UUID,
        notification_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Send notification to session streams

        Args:
            session_id: Session ID
            notification_type: Type of notification
            message: Notification message
            details: Additional details
        """
        await self.session_handler.send_session_status_update(
            session_id=str(session_id),
            status=notification_type,
            details={
                "message": message,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def update_session_metrics(self, session_id: UUID, metrics: Dict[str, Any]):
        """
        Update and broadcast session metrics

        Args:
            session_id: Session ID
            metrics: Metrics to broadcast
        """
        await self.session_handler.send_session_metrics_update(
            session_id=str(session_id), metrics=metrics
        )

    async def get_streaming_stats(self) -> Dict[str, Any]:
        """Get overall streaming statistics"""
        return await self.sse_manager.get_connection_stats()


# Global streaming service instance
streaming_service: Optional[StreamingService] = None


async def get_streaming_service() -> StreamingService:
    """Get or create global streaming service"""
    global streaming_service

    if streaming_service is None:
        streaming_service = StreamingService()
        await streaming_service.initialize()

    return streaming_service
