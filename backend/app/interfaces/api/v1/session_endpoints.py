"""
Session API Endpoints - Interview Session Management
Handles creating, managing, and interacting with interview sessions
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.shared.logging import get_logger, log_endpoint_call, log_error
from app.interfaces.schemas.session_schemas import (
    CreateSessionRequest,
    SessionResponse,
    SessionListResponse,
    MessageRequest,
    MessageResponse,
    ConversationHistoryResponse,
    SessionActionRequest,
    SessionMetricsResponse,
    UserSessionStatsResponse,
)
from app.domain.entities.session import (
    SessionStatus,
    MessageRole,
    MessageType,
    DifficultyLevel,
)
from app.domain.entities.user import User
from app.shared.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    BusinessLogicError,
    ConflictError,
)

# Import dependencies from user endpoints and database
from app.interfaces.api.v1.user_endpoints import get_current_user
from app.application.services.session_service import SessionService
from app.application.services.ai_service import AIService
from app.infrastructure.database.repositories.session_repository_impl import (
    PostgreSQLSessionRepository,
)
from app.infrastructure.database.repositories.user_repository_impl import (
    PostgreSQLUserRepository,
)
from app.infrastructure.database.config import get_db_session

# Router setup
router = APIRouter(prefix="/sessions", tags=["sessions"])
logger = get_logger(__name__)


# Dependency injection for session service
async def get_session_service(db=Depends(get_db_session)) -> SessionService:
    """Get session service with PostgreSQL repositories"""
    session_repository = PostgreSQLSessionRepository(db)
    user_repository = PostgreSQLUserRepository(db)
    return SessionService(session_repository, user_repository)


# Dependency injection for AI service
async def get_ai_service() -> AIService:
    """Get AI service for intelligent interview interactions"""
    return AIService()


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_request: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
    ai_service: AIService = Depends(get_ai_service),
):
    """Create a new interview session with AI integration"""
    log_endpoint_call(logger, "/sessions", "POST", user_id=str(current_user.user_id))

    try:
        # Create session using service
        created_session = await session_service.create_session(
            user_id=current_user.user_id,
            topic=session_request.config.topic,
            difficulty_level=session_request.config.difficulty_level,
            session_config={
                "max_duration_minutes": session_request.config.max_duration_minutes,
                "enable_hints": session_request.config.enable_hints,
                "enable_real_time_feedback": session_request.config.enable_real_time_feedback,
                "custom_requirements": session_request.config.custom_requirements,
            },
            metadata={},
        )

        # Start AI interview
        ai_response = await ai_service.start_interview_session(
            session=created_session,
            user_context={
                "user_preferences": (
                    current_user.preferences.__dict__
                    if current_user.preferences
                    else {}
                ),
                "experience_level": (
                    getattr(
                        current_user.preferences, "difficulty_level", "intermediate"
                    )
                    if current_user.preferences
                    else "intermediate"
                ),
            },
        )

        # Add initial AI question as a message
        if ai_response.get("question"):
            await session_service.add_message_to_session(
                session_id=created_session.session_id,
                role="ASSISTANT",
                content=ai_response["question"],
                message_type="QUESTION",
                metadata={
                    "ai_generated": True,
                    "question_type": "opening",
                    "context": ai_response.get("context", ""),
                    "expected_topics": ai_response.get("expected_topics", []),
                },
            )

        logger.info(
            "Session created successfully with AI integration",
            extra={
                "user_id": str(current_user.user_id),
                "session_id": str(created_session.session_id),
                "topic": created_session.topic,
                "difficulty": created_session.difficulty_level,
                "ai_question_generated": bool(ai_response.get("question")),
            },
        )

        return SessionResponse.from_entity(created_session)

    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        log_error(logger, e, context="create_session")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}",
        )


@router.get("/", response_model=SessionListResponse)
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: Optional[SessionStatus] = Query(default=None),
):
    """Get user's interview sessions"""
    log_endpoint_call(logger, "/sessions", "GET", user_id=str(current_user.user_id))

    try:
        sessions = await session_service.get_user_sessions(
            current_user.user_id, limit, offset
        )

        # Filter by status if provided
        if status_filter:
            sessions = [s for s in sessions if s.status == status_filter]

        session_responses = [SessionResponse.from_entity(s) for s in sessions]

        return SessionListResponse(
            sessions=session_responses,
            total_count=len(session_responses),
            has_more=len(sessions) == limit,
        )

    except Exception as e:
        log_error(logger, e, context="get_user_sessions")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sessions: {str(e)}",
        )


@router.get("/active", response_model=Optional[SessionResponse])
async def get_active_session(
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Get user's active session (if any)"""
    log_endpoint_call(
        logger, "/sessions/active", "GET", user_id=str(current_user.user_id)
    )

    try:
        active_session = await session_service.get_user_active_session(
            current_user.user_id
        )

        if active_session:
            return SessionResponse.from_entity(active_session)
        return None

    except Exception as e:
        log_error(logger, e, context="get_active_session")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve active session: {str(e)}",
        )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Get specific session details"""
    log_endpoint_call(
        logger, f"/sessions/{session_id}", "GET", user_id=str(current_user.user_id)
    )

    try:
        session = await session_service.get_session(session_id)

        if session.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session",
            )

        return SessionResponse.from_entity(session)

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except Exception as e:
        log_error(logger, e, context="get_session")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session: {str(e)}",
        )


@router.post("/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: UUID,
    message_request: MessageRequest,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
    ai_service: AIService = Depends(get_ai_service),
):
    """Send a message in the interview session with AI response"""
    log_endpoint_call(
        logger,
        f"/sessions/{session_id}/messages",
        "POST",
        user_id=str(current_user.user_id),
    )

    try:
        # Get session and verify access
        session = await session_service.get_session(session_id)

        if session.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session",
            )

        # Add user message via service
        user_message = await session_service.add_message_to_session(
            session_id=session_id,
            role="USER",
            content=message_request.content,
            message_type=(
                message_request.message_type.value
                if message_request.message_type
                else "TEXT"
            ),
            metadata=message_request.metadata,
        )

        # Process user response with AI
        ai_response = await ai_service.process_user_response(
            session_id=session_id,
            user_message=message_request.content,
            message_type=(
                message_request.message_type.value
                if message_request.message_type
                else "answer"
            ),
        )

        # Add AI response as a message
        ai_message_content = ""
        ai_metadata = {
            "ai_generated": True,
            "response_type": ai_response.get("type", "general"),
        }

        if ai_response.get("type") == "feedback_and_continue":
            # Combine feedback and next question
            feedback = ai_response.get("feedback", "")
            next_question = ai_response.get("message", "")
            ai_message_content = f"{feedback}\n\n{next_question}"
            ai_metadata.update(
                {
                    "feedback": feedback,
                    "next_question": next_question,
                    "strengths": ai_response.get("strengths", []),
                    "areas_for_improvement": ai_response.get(
                        "areas_for_improvement", []
                    ),
                }
            )
        elif ai_response.get("type") == "clarification":
            ai_message_content = ai_response.get("message", "")
            ai_metadata.update(
                {
                    "guidance": ai_response.get("guidance", ""),
                    "context": ai_response.get("context", ""),
                }
            )
        elif ai_response.get("type") == "follow_up":
            ai_message_content = ai_response.get("message", "")
            ai_metadata.update(
                {
                    "focus_areas": ai_response.get("focus_areas", []),
                    "context": ai_response.get("context", ""),
                }
            )
        elif ai_response.get("type") == "topic_transition":
            ai_message_content = ai_response.get("message", "")
            ai_metadata.update(
                {
                    "new_topic": ai_response.get("new_topic", ""),
                    "context": ai_response.get("context", ""),
                }
            )
        elif ai_response.get("type") == "interview_complete":
            ai_message_content = ai_response.get("message", "")
            ai_metadata.update(
                {
                    "interview_complete": True,
                    "detailed_feedback": ai_response.get("detailed_feedback", {}),
                    "performance_summary": ai_response.get("performance_summary", {}),
                    "recommendations": ai_response.get("recommendations", []),
                }
            )

            # Update session status to completed
            await session_service.update_session_status(session_id, "COMPLETED")
        else:
            ai_message_content = ai_response.get(
                "message", "Thank you for your response. Let's continue."
            )

        # Add AI message to session
        await session_service.add_message_to_session(
            session_id=session_id,
            role="ASSISTANT",
            content=ai_message_content,
            message_type="TEXT",
            metadata=ai_metadata,
        )

        logger.info(
            "Message processed with AI response",
            extra={
                "session_id": str(session_id),
                "user_id": str(current_user.user_id),
                "ai_response_type": ai_response.get("type", "general"),
                "message_type": (
                    message_request.message_type.value
                    if message_request.message_type
                    else "TEXT"
                ),
            },
        )

        # Return the user message (as before)
        return MessageResponse(
            message_id=user_message.message_id,
            role=user_message.role,
            content=user_message.content,
            message_type=user_message.message_type,
            timestamp=user_message.timestamp,
            metadata=user_message.metadata,
            tokens_used=user_message.tokens_used,
        )

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        log_error(logger, e, context="send_message")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}",
        )


@router.get("/{session_id}/messages", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
    limit: Optional[int] = Query(default=None, ge=1, le=500),
):
    """Get conversation history for a session"""
    log_endpoint_call(
        logger,
        f"/sessions/{session_id}/messages",
        "GET",
        user_id=str(current_user.user_id),
    )

    try:
        # Get session and verify access
        session = await session_service.get_session(session_id)

        if session.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session",
            )

        # Get conversation history via service
        messages = await session_service.get_session_messages(session_id, limit)

        message_responses = [
            MessageResponse(
                message_id=msg.message_id,
                role=msg.role,
                content=msg.content,
                message_type=msg.message_type,
                timestamp=msg.timestamp,
                metadata=msg.metadata,
                tokens_used=msg.tokens_used,
            )
            for msg in messages
        ]

        return ConversationHistoryResponse(
            session_id=session_id,
            messages=message_responses,
            total_messages=len(session.messages),
        )

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except Exception as e:
        log_error(logger, e, context="get_conversation_history")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation: {str(e)}",
        )


@router.post("/{session_id}/actions")
async def session_action(
    session_id: UUID,
    action_request: SessionActionRequest,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Perform session actions: extend, complete, or abandon"""
    log_endpoint_call(
        logger,
        f"/sessions/{session_id}/actions",
        "POST",
        user_id=str(current_user.user_id),
        extra={"action": action_request.action},
    )

    try:
        # Get session and verify access
        session = await session_service.get_session(session_id)

        if session.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session",
            )

        # Perform action via service
        if action_request.action == "complete":
            updated_session = await session_service.update_session_status(
                session_id, "COMPLETED"
            )

            # Clean up AI resources
            try:
                ai_service_instance = await get_ai_service()
                await ai_service_instance.cleanup_session(session_id)
            except Exception as cleanup_error:
                logger.warning(
                    f"AI cleanup failed for session {session_id}: {cleanup_error}"
                )

            message = "Session completed successfully"
        elif action_request.action == "abandon":
            updated_session = await session_service.update_session_status(
                session_id, "ABANDONED"
            )

            # Clean up AI resources
            try:
                ai_service_instance = await get_ai_service()
                await ai_service_instance.cleanup_session(session_id)
            except Exception as cleanup_error:
                logger.warning(
                    f"AI cleanup failed for session {session_id}: {cleanup_error}"
                )

            message = "Session abandoned"
        elif action_request.action == "extend":
            # For extend, we need to modify session directly (not implemented in service yet)
            if session.status.value != "ACTIVE":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Can only extend active sessions",
                )
            # TODO: Implement extend functionality in service
            updated_session = session
            message = f"Session extended by {action_request.additional_minutes} minutes"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {action_request.action}",
            )

        logger.info(
            f"Session action {action_request.action} performed",
            extra={"session_id": str(session_id), "user_id": str(current_user.user_id)},
        )

        return {
            "message": message,
            "session": SessionResponse.from_entity(updated_session),
        }

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        log_error(logger, e, context="session_action")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform action: {str(e)}",
        )


@router.get("/{session_id}/metrics", response_model=SessionMetricsResponse)
async def get_session_metrics(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Get session metrics and analytics"""
    log_endpoint_call(
        logger,
        f"/sessions/{session_id}/metrics",
        "GET",
        user_id=str(current_user.user_id),
    )

    try:
        # Get session and verify access
        session = await session_service.get_session(session_id)

        if session.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session",
            )

        # Calculate metrics from session data
        metrics = {
            "session_id": str(session.session_id),
            "status": session.status.value,
            "topic": session.topic,
            "difficulty": session.difficulty_level,
            "duration_seconds": session.total_duration,
            "total_messages": len(session.messages),
            "user_messages": len(
                [m for m in session.messages if m.role.value == "USER"]
            ),
            "assistant_messages": len(
                [m for m in session.messages if m.role.value == "ASSISTANT"]
            ),
            "total_tokens_used": sum(m.tokens_used or 0 for m in session.messages),
            "started_at": (
                session.started_at.isoformat() if session.started_at else None
            ),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        }

        return SessionMetricsResponse(
            session_id=UUID(metrics["session_id"]),
            status=SessionStatus(metrics["status"]),
            topic=metrics["topic"],
            difficulty=DifficultyLevel(metrics["difficulty"]),
            duration_seconds=metrics["duration_seconds"],
            total_messages=metrics["total_messages"],
            user_messages=metrics["user_messages"],
            assistant_messages=metrics["assistant_messages"],
            total_tokens_used=metrics["total_tokens_used"],
            started_at=(
                datetime.fromisoformat(metrics["started_at"])
                if metrics["started_at"]
                else None
            ),
            ended_at=(
                datetime.fromisoformat(metrics["ended_at"])
                if metrics["ended_at"]
                else None
            ),
        )

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except Exception as e:
        log_error(logger, e, context="get_session_metrics")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics: {str(e)}",
        )


@router.get("/stats/user", response_model=UserSessionStatsResponse)
async def get_user_session_stats(
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Get comprehensive session statistics for the user"""
    log_endpoint_call(
        logger, "/sessions/stats/user", "GET", user_id=str(current_user.user_id)
    )

    try:
        stats = await session_service.get_user_session_stats(current_user.user_id)
        return UserSessionStatsResponse(**stats)

    except Exception as e:
        log_error(logger, e, context="get_user_session_stats")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user stats: {str(e)}",
        )


# Health check
@router.get("/health")
async def session_health_check():
    """Session service health check"""
    log_endpoint_call(logger, "/sessions/health", "GET")
    return {"status": "healthy", "service": "session-service"}


# AI-powered endpoints
@router.post("/{session_id}/ai/hint")
async def request_hint(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
    session_service: SessionService = Depends(get_session_service),
):
    """Request an AI-generated hint for the current question"""
    log_endpoint_call(
        logger,
        f"/sessions/{session_id}/ai/hint",
        "POST",
        user_id=str(current_user.user_id),
    )

    try:
        # Verify session access
        session = await session_service.get_session(session_id)
        if session.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session",
            )

        # Get current question from recent messages
        messages = await session_service.get_session_messages(session_id, limit=5)
        current_question = None
        for message in reversed(messages):
            if message.role.value == "ASSISTANT" and "?" in message.content:
                current_question = message.content
                break

        if not current_question:
            current_question = "Please provide more details about your approach."

        # Generate hint
        hint_response = await ai_service.request_hint(
            session_id=session_id,
            current_question=current_question,
            user_context="User requested a hint",
        )

        return hint_response

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except Exception as e:
        log_error(logger, e, context="request_hint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate hint: {str(e)}",
        )


@router.get("/{session_id}/ai/insights")
async def get_ai_insights(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
    session_service: SessionService = Depends(get_session_service),
):
    """Get AI insights about session progress and performance"""
    log_endpoint_call(
        logger,
        f"/sessions/{session_id}/ai/insights",
        "GET",
        user_id=str(current_user.user_id),
    )

    try:
        # Verify session access
        session = await session_service.get_session(session_id)
        if session.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session",
            )

        # Get AI insights
        insights = await ai_service.get_session_insights(session_id)
        return insights

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except Exception as e:
        log_error(logger, e, context="get_ai_insights")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI insights: {str(e)}",
        )


@router.get("/{session_id}/ai/feedback")
async def get_ai_feedback(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
    session_service: SessionService = Depends(get_session_service),
):
    """Get comprehensive AI feedback for the interview"""
    log_endpoint_call(
        logger,
        f"/sessions/{session_id}/ai/feedback",
        "GET",
        user_id=str(current_user.user_id),
    )

    try:
        # Verify session access
        session = await session_service.get_session(session_id)
        if session.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session",
            )

        # Get comprehensive feedback
        feedback = await ai_service.get_interview_feedback(session_id)
        return feedback

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except Exception as e:
        log_error(logger, e, context="get_ai_feedback")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI feedback: {str(e)}",
        )


@router.get("/{session_id}/ai/summary")
async def get_conversation_summary(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
    session_service: SessionService = Depends(get_session_service),
):
    """Get AI-generated conversation summary"""
    log_endpoint_call(
        logger,
        f"/sessions/{session_id}/ai/summary",
        "GET",
        user_id=str(current_user.user_id),
    )

    try:
        # Verify session access
        session = await session_service.get_session(session_id)
        if session.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session",
            )

        # Get conversation summary
        summary = await ai_service.get_conversation_summary(session_id)
        return summary

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except Exception as e:
        log_error(logger, e, context="get_conversation_summary")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation summary: {str(e)}",
        )
