"""
Session Streaming API Endpoints
Real-time streaming for AI responses using Server-Sent Events (SSE)
"""

import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Dict, Any
from uuid import UUID

from app.shared.logging import get_logger, log_endpoint_call, log_error
from app.interfaces.schemas.session_schemas import (
    MessageRequest,
    CreateSessionRequest,
    CreateSessionWithStartRequest,
    SessionResponse,
    DetailedSessionResponse,
    StartSessionResponse,
    SessionListResponse,
)
from app.domain.entities.user import User
from app.domain.entities.session import SessionStatus
from app.shared.exceptions import (
    ConflictError,
    ResourceNotFoundError,
    ValidationError,
    BusinessRuleError,
)

# Import dependencies
from app.interfaces.api.v1.user_endpoints import get_current_user
from app.application.services.session_service import SessionService
from app.application.services.user_service import UserService
from app.application.services.ai_service import AIService
from app.infrastructure.database.repositories.session_repository_impl import (
    PostgreSQLSessionRepository,
)
from app.infrastructure.database.repositories.user_repository_impl import (
    PostgreSQLUserRepository,
)
from app.infrastructure.database.config import get_db_session

# Router setup
router = APIRouter(prefix="/sessions", tags=["session-streaming"])
logger = get_logger(__name__)


# Global AI service instance (singleton pattern with instance tracking)
_ai_service_instance = None
_ai_service_instance_id = None


# Dependency injection
async def get_session_service(db=Depends(get_db_session)) -> SessionService:
    """Get session service with PostgreSQL repositories"""
    session_repository = PostgreSQLSessionRepository(db)
    user_repository = PostgreSQLUserRepository(db)
    return SessionService(session_repository, user_repository)


async def get_user_service(db=Depends(get_db_session)) -> UserService:
    """Get user service with PostgreSQL repositories"""
    from app.infrastructure.database.repositories.user_analytics_repository import (
        SQLAlchemyUserAnalyticsRepository,
    )
    from app.application.services.user_analytics_service import UserAnalyticsService
    
    user_repository = PostgreSQLUserRepository(db)
    analytics_repository = SQLAlchemyUserAnalyticsRepository(db)
    analytics_service = UserAnalyticsService(analytics_repository)
    return UserService(user_repository, analytics_service)


async def get_ai_service() -> AIService:
    """Get AI service instance (singleton to maintain memory state)"""
    global _ai_service_instance, _ai_service_instance_id

    if _ai_service_instance is None:
        _ai_service_instance = AIService()
        _ai_service_instance_id = _ai_service_instance.orchestrator.instance_id
        logger.info(
            f"Created singleton AIService instance with ID: {_ai_service_instance_id}"
        )
    else:
        logger.debug(
            f"Reusing existing AIService singleton with ID: {_ai_service_instance_id}"
        )

    return _ai_service_instance


# ===============================
# SESSION MANAGEMENT ENDPOINTS
# ===============================


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_request: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
    user_service: UserService = Depends(get_user_service),
):
    """Create a new interview session (without starting it)"""
    log_endpoint_call(logger, "/sessions", "POST", user_id=str(current_user.user_id))

    try:
        # Check interview limits before creating session
        can_create, reason = await user_service.check_interview_creation_limits(
            current_user.user_id
        )

        if not can_create:
            logger.warning(
                f"Interview creation blocked for user {current_user.user_id}: {reason}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Interview limit exceeded",
                    "message": reason,
                    "upgrade_required": True if "limit" in reason.lower() else False,
                },
            )

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

        # Record interview creation (increment counters)
        await user_service.record_interview_creation(current_user.user_id)

        logger.info(
            "Session created successfully",
            extra={
                "user_id": str(current_user.user_id),
                "session_id": str(created_session.session_id),
                "topic": created_session.config.topic,
                "difficulty": created_session.config.difficulty_level,
            },
        )

        return SessionResponse.from_entity(created_session)

    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/start", response_model=StartSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_and_start_session(
    session_request: CreateSessionWithStartRequest,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
    user_service: UserService = Depends(get_user_service),
    ai_service: AIService = Depends(get_ai_service),
):
    """Create and start a new interview session with opening question"""
    log_endpoint_call(logger, "/sessions/start", "POST", user_id=str(current_user.user_id))

    try:
        # Check interview limits before creating session
        can_create, reason = await user_service.check_interview_creation_limits(
            current_user.user_id
        )

        if not can_create:
            logger.warning(
                f"Interview creation blocked for user {current_user.user_id}: {reason}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Interview limit exceeded",
                    "message": reason,
                    "upgrade_required": True if "limit" in reason.lower() else False,
                },
            )

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

        # Generate opening question using AI service
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

        # Add the opening question as an AI message
        opening_message = await session_service.add_message_to_session(
            session_id=created_session.session_id,
            role="ASSISTANT",
            content=ai_response.get("question", ""),
            message_type="QUESTION",
            metadata={
                "type": "opening_question",
                "expected_topics": ai_response.get("expected_topics", []),
                "context": ai_response.get("context", ""),
            },
        )

        # Record interview creation (increment counters)
        await user_service.record_interview_creation(current_user.user_id)

        logger.info(
            "Session created and started successfully",
            extra={
                "user_id": str(current_user.user_id),
                "session_id": str(created_session.session_id),
                "topic": created_session.config.topic,
                "difficulty": created_session.config.difficulty_level,
                "opening_question_length": len(ai_response.get("question", "")),
            },
        )

        return StartSessionResponse.from_session_and_message(
            created_session, opening_message, ai_response
        )

    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
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


@router.get("/{session_id}", response_model=DetailedSessionResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Get session details with full chat history and feedback"""
    log_endpoint_call(
        logger,
        f"/sessions/{session_id}",
        "GET",
        user_id=str(current_user.user_id),
    )

    try:
        # Get session with automatic timeout check
        session = await session_service.get_session_with_timeout_check(session_id)

        if session.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session",
            )

        # TODO: Get feedback from feedback repository
        feedback = None  # We'll implement this when we create the feedback repository

        return DetailedSessionResponse.from_entity(session, feedback)

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


@router.get("/", response_model=SessionListResponse)
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
    limit: int = 20,
    offset: int = 0,
):
    """Get user's interview sessions"""
    log_endpoint_call(logger, "/sessions", "GET", user_id=str(current_user.user_id))

    try:
        sessions = await session_service.get_user_sessions(
            current_user.user_id, limit, offset
        )

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


@router.post("/{session_id}/start")
async def start_interview(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
    ai_service: AIService = Depends(get_ai_service),
):
    """Start the interview session and get the opening question"""
    log_endpoint_call(
        logger,
        f"/sessions/{session_id}/start",
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

        # Check if session is already started
        if session.status != SessionStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is {session.status.value}, cannot start",
            )

        # Generate opening question using AI service
        ai_response = await ai_service.start_interview_session(
            session=session,
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

        # Add the opening question as an AI message
        opening_message = await session_service.add_message_to_session(
            session_id=session_id,
            role="ASSISTANT",
            content=ai_response.get("question", ""),
            message_type="QUESTION",
            metadata={
                "type": "opening_question",
                "expected_topics": ai_response.get("expected_topics", []),
                "context": ai_response.get("context", ""),
            },
        )

        logger.info(
            "Interview started successfully",
            extra={
                "session_id": str(session_id),
                "user_id": str(current_user.user_id),
                "topic": session.config.topic,
            },
        )

        return {
            "message": "Interview started successfully",
            "opening_question": ai_response.get("question", ""),
            "message_id": str(opening_message.message_id),
            "expected_topics": ai_response.get("expected_topics", []),
            "session_status": "active",
        }

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except Exception as e:
        log_error(logger, e, context="start_interview")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start interview: {str(e)}",
        )


@router.post("/{session_id}/end")
async def end_interview(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
    reason: str = "completed",
):
    """End the interview session (mark as completed or abandoned)"""
    log_endpoint_call(
        logger,
        f"/sessions/{session_id}/end",
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

        # Check if session can be ended
        if session.status not in [SessionStatus.ACTIVE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is already {session.status.value}",
            )

        # Update session status
        if reason.lower() in ["completed", "complete"]:
            updated_session = await session_service.update_session_status(
                session_id, "COMPLETED"
            )
        elif reason.lower() in ["abandoned", "abandon"]:
            updated_session = await session_service.update_session_status(
                session_id, "ABANDONED"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reason. Use 'completed' or 'abandoned'",
            )

        logger.info(
            "Interview ended successfully",
            extra={
                "session_id": str(session_id),
                "user_id": str(current_user.user_id),
                "reason": reason,
                "status": updated_session.status.value,
                "duration": updated_session.total_duration,
            },
        )

        return {
            "message": f"Interview {reason} successfully",
            "session_id": str(session_id),
            "status": updated_session.status.value,
            "duration_seconds": updated_session.total_duration,
            "ended_at": (
                updated_session.ended_at.isoformat()
                if updated_session.ended_at
                else None
            ),
        }

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except Exception as e:
        log_error(logger, e, context="end_interview")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end interview: {str(e)}",
        )


@router.put("/{session_id}/status")
async def update_session_status(
    session_id: UUID,
    status_update: Dict[str, str],
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Update session status (pause/resume/complete/abandon)"""
    log_endpoint_call(
        logger,
        f"/sessions/{session_id}/status",
        "PUT",
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

        new_status = status_update.get("status", "").upper()
        if not new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status is required",
            )

        # Update session status
        updated_session = await session_service.update_session_status(
            session_id, new_status
        )

        logger.info(
            "Session status updated",
            extra={
                "session_id": str(session_id),
                "user_id": str(current_user.user_id),
                "old_status": session.status.value,
                "new_status": updated_session.status.value,
            },
        )

        return {
            "message": "Session status updated successfully",
            "session_id": str(session_id),
            "old_status": session.status.value,
            "new_status": updated_session.status.value,
            "updated_at": updated_session.updated_at.isoformat(),
        }

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        log_error(logger, e, context="update_session_status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session status: {str(e)}",
        )


# ===============================
# STREAMING CHAT ENDPOINTS
# ===============================


@router.post("/{session_id}/chat/stream")
async def stream_chat_response(
    session_id: UUID,
    message_request: MessageRequest,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
    ai_service: AIService = Depends(get_ai_service),
):
    """
    Stream AI response in real-time using Server-Sent Events

    This endpoint:
    1. Adds user message to session
    2. Streams AI response token by token
    3. Saves complete AI response when done
    """
    log_endpoint_call(
        logger,
        f"/sessions/{session_id}/chat/stream",
        "POST",
        user_id=str(current_user.user_id),
    )

    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate SSE stream for the chat response"""
        try:
            # Verify session access
            session = await session_service.get_session(session_id)
            if session.user_id != current_user.user_id:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Access denied to session'})}\n\n"
                return

            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Processing your message...'})}\n\n"

            # Add user message to session
            user_message = await session_service.add_message_to_session(
                session_id=session_id,
                role="USER",
                content=message_request.content,
                message_type=(
                    message_request.message_type.value
                    if message_request.message_type
                    else "TEXT"
                ),
                metadata=message_request.metadata or {},
            )

            # Send user message confirmation
            yield f"data: {json.dumps({'type': 'user_message_saved', 'message_id': str(user_message.message_id)})}\n\n"

            # Send analysis status
            yield f"data: {json.dumps({'type': 'status', 'message': 'AI is analyzing your response...'})}\n\n"

            # Stream AI response
            complete_response = ""
            async for chunk in ai_service.process_user_response_stream(
                session_id=session_id,
                user_message=message_request.content,
                message_type=(
                    message_request.message_type.value
                    if message_request.message_type
                    else "TEXT"
                ),
            ):
                if chunk.get("type") == "content":
                    # Stream content tokens
                    content = chunk.get("content", "")
                    complete_response += content
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                elif chunk.get("type") == "status":
                    # Stream status updates
                    yield f"data: {json.dumps(chunk)}\n\n"

            # Save complete AI response
            ai_message = await session_service.add_message_to_session(
                session_id=session_id,
                role="ASSISTANT",
                content=complete_response,
                message_type="RESPONSE",
                metadata={"generated_via": "streaming"},
            )

            # Send completion
            yield f"data: {json.dumps({'type': 'complete', 'ai_message_id': str(ai_message.message_id), 'total_tokens': len(complete_response.split())})}\n\n"

        except ResourceNotFoundError as e:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Session not found'})}\n\n"
        except ValidationError as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        except Exception as e:
            log_error(logger, e, context="stream_chat_response")
            yield f"data: {json.dumps({'type': 'error', 'message': 'An unexpected error occurred'})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )


@router.get("/{session_id}/chat/stream/test")
async def test_stream(session_id: UUID):
    """Test endpoint to verify SSE streaming works"""

    async def generate_test() -> AsyncGenerator[str, None]:
        """Generate test SSE messages"""
        for i in range(5):
            yield f"data: {json.dumps({'type': 'test', 'count': i, 'message': f'Test message {i}'})}\n\n"
            await asyncio.sleep(1)  # Simulate delay

        yield f"data: {json.dumps({'type': 'complete', 'message': 'Test complete'})}\n\n"

    return StreamingResponse(
        generate_test(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/debug/ai-instance")
async def debug_ai_instance(ai_service: AIService = Depends(get_ai_service)):
    """Debug endpoint to check AIService instance details"""
    return {
        "ai_service_id": id(ai_service),
        "orchestrator_instance_id": ai_service.orchestrator.instance_id,
        "session_manager_instance_id": ai_service.orchestrator.session_manager.instance_id,
        "active_sessions": await ai_service.orchestrator.session_manager.get_active_sessions(),
        "message": "This should be the same across all requests",
    }


@router.get("/{session_id}/debug/memory")
async def debug_session_memory(
    session_id: UUID, ai_service: AIService = Depends(get_ai_service)
):
    """Debug session memory contents"""
    debug_info = await ai_service.orchestrator.debug_memory_contents(str(session_id))
    return debug_info
