"""
Async Session API Endpoints - Non-blocking Interview Session Management
Handles session operations with async task processing and real-time updates
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.shared.logging import get_logger, log_endpoint_call, log_error
from app.interfaces.schemas.session_schemas import (
    CreateSessionRequest,
    SessionResponse,
    SessionListResponse,
    MessageRequest,
    AsyncMessageResponse,
    TaskStatusResponse,
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

# Import dependencies
from app.interfaces.api.v1.user_endpoints import get_current_user
from app.application.services.session_service import SessionService
from app.infrastructure.database.repositories.session_repository_impl import (
    PostgreSQLSessionRepository,
)
from app.infrastructure.database.repositories.user_repository_impl import (
    PostgreSQLUserRepository,
)
from app.infrastructure.database.config import get_db_session

# Import async task infrastructure
from app.infrastructure.tasks.task_queue import get_task_manager, TaskType
from app.infrastructure.tasks.websocket_manager import get_task_websocket_handler

# Router setup
router = APIRouter(prefix="/async/sessions", tags=["async-sessions"])
logger = get_logger(__name__)


# Dependency injection for session service
async def get_session_service(db=Depends(get_db_session)) -> SessionService:
    """Get session service with PostgreSQL repositories"""
    session_repository = PostgreSQLSessionRepository(db)
    user_repository = PostgreSQLUserRepository(db)
    return SessionService(session_repository, user_repository)


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session_async(
    session_request: CreateSessionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Create a new interview session with async AI initialization"""
    log_endpoint_call(
        logger, "/async/sessions", "POST", user_id=str(current_user.user_id)
    )

    try:
        # Create session using service (quick operation)
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

        # Queue AI initialization as background task
        task_handler = await get_task_websocket_handler()
        task_id = await task_handler.start_task_with_websocket(
            task_type=TaskType.AI_START_INTERVIEW,
            session_id=str(created_session.session_id),
            user_id=str(current_user.user_id),
            payload={
                "session": created_session.__dict__,
                "user_context": {
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
            },
            priority=1,  # High priority for session creation
        )

        logger.info(
            "Session created with async AI initialization",
            extra={
                "user_id": str(current_user.user_id),
                "session_id": str(created_session.session_id),
                "topic": created_session.topic,
                "difficulty": created_session.difficulty_level,
                "ai_task_id": task_id,
            },
        )

        return SessionResponse.from_entity(created_session)

    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        log_error(logger, e, context="create_session_async")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}",
        )


@router.post("/{session_id}/messages", response_model=AsyncMessageResponse)
async def send_message_async(
    session_id: UUID,
    message_request: MessageRequest,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Send a message in the interview session with async AI processing"""
    log_endpoint_call(
        logger,
        f"/async/sessions/{session_id}/messages",
        "POST",
        user_id=str(current_user.user_id),
    )

    try:
        # Get session and verify access (quick operation)
        session = await session_service.get_session(session_id)

        if session.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session",
            )

        # Add user message via service (quick operation)
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

        # Queue AI processing as background task
        task_handler = await get_task_websocket_handler()
        task_id = await task_handler.start_task_with_websocket(
            task_type=TaskType.AI_PROCESS_RESPONSE,
            session_id=str(session_id),
            user_id=str(current_user.user_id),
            payload={
                "session_id": str(session_id),
                "user_message": message_request.content,
                "message_type": (
                    message_request.message_type.value
                    if message_request.message_type
                    else "answer"
                ),
            },
            priority=1,  # High priority for user interactions
        )

        logger.info(
            "Message queued for async AI processing",
            extra={
                "session_id": str(session_id),
                "user_id": str(current_user.user_id),
                "message_type": (
                    message_request.message_type.value
                    if message_request.message_type
                    else "TEXT"
                ),
                "ai_task_id": task_id,
            },
        )

        # Return immediate response with task info
        return AsyncMessageResponse(
            message_id=user_message.message_id,
            role=user_message.role,
            content=user_message.content,
            message_type=user_message.message_type,
            timestamp=user_message.timestamp,
            metadata=user_message.metadata,
            tokens_used=user_message.tokens_used,
            task_id=task_id,
            task_status="pending",
            estimated_completion_seconds=180,  # 3 minutes estimate
        )

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        log_error(logger, e, context="send_message_async")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}",
        )


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get status of a background task"""
    log_endpoint_call(
        logger,
        f"/async/sessions/tasks/{task_id}",
        "GET",
        user_id=str(current_user.user_id),
    )

    try:
        task_manager = await get_task_manager()
        task = await task_manager.get_task(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        # Verify user has access to this task
        if task.user_id != str(current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this task",
            )

        progress = await task_manager.get_task_progress(task_id)

        return TaskStatusResponse(
            task_id=task_id,
            status=task.status.value,
            task_type=task.task_type.value,
            session_id=UUID(task.session_id),
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            progress=(
                {
                    "current_step": progress.current_step,
                    "completed_steps": progress.completed_steps,
                    "total_steps": progress.total_steps,
                    "percentage": progress.percentage,
                    "message": progress.message,
                    "details": progress.details,
                }
                if progress
                else None
            ),
            result=task.result,
            error=task.error,
            retry_count=task.retry_count,
        )

    except Exception as e:
        log_error(logger, e, context="get_task_status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}",
        )


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """Cancel a pending background task"""
    log_endpoint_call(
        logger,
        f"/async/sessions/tasks/{task_id}/cancel",
        "POST",
        user_id=str(current_user.user_id),
    )

    try:
        task_manager = await get_task_manager()
        task = await task_manager.get_task(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        # Verify user has access to this task
        if task.user_id != str(current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this task",
            )

        success = await task_manager.cancel_task(task_id)

        if success:
            return {"message": "Task cancelled successfully", "task_id": task_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task cannot be cancelled (may be already processing or completed)",
            )

    except Exception as e:
        log_error(logger, e, context="cancel_task")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}",
        )


@router.get("/{session_id}/tasks", response_model=List[TaskStatusResponse])
async def get_session_tasks(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Get all tasks for a session"""
    log_endpoint_call(
        logger,
        f"/async/sessions/{session_id}/tasks",
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

        task_manager = await get_task_manager()
        task_ids = await task_manager.get_session_tasks(str(session_id))

        tasks = []
        for task_id in task_ids:
            task = await task_manager.get_task(task_id)
            if task:
                progress = await task_manager.get_task_progress(task_id)

                tasks.append(
                    TaskStatusResponse(
                        task_id=task_id,
                        status=task.status.value,
                        task_type=task.task_type.value,
                        session_id=UUID(task.session_id),
                        created_at=task.created_at,
                        started_at=task.started_at,
                        completed_at=task.completed_at,
                        progress=(
                            {
                                "current_step": progress.current_step,
                                "completed_steps": progress.completed_steps,
                                "total_steps": progress.total_steps,
                                "percentage": progress.percentage,
                                "message": progress.message,
                                "details": progress.details,
                            }
                            if progress
                            else None
                        ),
                        result=task.result,
                        error=task.error,
                        retry_count=task.retry_count,
                    )
                )

        return tasks

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except Exception as e:
        log_error(logger, e, context="get_session_tasks")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session tasks: {str(e)}",
        )


# AI-powered async endpoints
@router.post("/{session_id}/ai/hint/async", response_model=TaskStatusResponse)
async def request_hint_async(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Request an AI-generated hint asynchronously"""
    log_endpoint_call(
        logger,
        f"/async/sessions/{session_id}/ai/hint/async",
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

        # Queue hint generation task
        task_handler = await get_task_websocket_handler()
        task_id = await task_handler.start_task_with_websocket(
            task_type=TaskType.AI_GENERATE_HINT,
            session_id=str(session_id),
            user_id=str(current_user.user_id),
            payload={
                "session_id": str(session_id),
                "current_question": current_question,
                "user_context": "User requested a hint",
            },
            priority=2,  # Medium priority for hints
        )

        return TaskStatusResponse(
            task_id=task_id,
            status="pending",
            task_type="ai_generate_hint",
            session_id=session_id,
            created_at=datetime.utcnow(),
            started_at=None,
            completed_at=None,
            progress=None,
            result=None,
            error=None,
            retry_count=0,
        )

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except Exception as e:
        log_error(logger, e, context="request_hint_async")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue hint generation: {str(e)}",
        )


@router.get("/{session_id}/ai/insights/async", response_model=TaskStatusResponse)
async def get_ai_insights_async(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Get AI insights about session progress asynchronously"""
    log_endpoint_call(
        logger,
        f"/async/sessions/{session_id}/ai/insights/async",
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

        # Queue insights generation task
        task_handler = await get_task_websocket_handler()
        task_id = await task_handler.start_task_with_websocket(
            task_type=TaskType.AI_GET_INSIGHTS,
            session_id=str(session_id),
            user_id=str(current_user.user_id),
            payload={"session_id": str(session_id)},
            priority=2,  # Medium priority for insights
        )

        return TaskStatusResponse(
            task_id=task_id,
            status="pending",
            task_type="ai_get_insights",
            session_id=session_id,
            created_at=datetime.utcnow(),
            started_at=None,
            completed_at=None,
            progress=None,
            result=None,
            error=None,
            retry_count=0,
        )

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except Exception as e:
        log_error(logger, e, context="get_ai_insights_async")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue insights generation: {str(e)}",
        )


@router.get("/{session_id}/ai/feedback/async", response_model=TaskStatusResponse)
async def get_ai_feedback_async(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Get comprehensive AI feedback asynchronously"""
    log_endpoint_call(
        logger,
        f"/async/sessions/{session_id}/ai/feedback/async",
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

        # Queue feedback generation task
        task_handler = await get_task_websocket_handler()
        task_id = await task_handler.start_task_with_websocket(
            task_type=TaskType.AI_GET_FEEDBACK,
            session_id=str(session_id),
            user_id=str(current_user.user_id),
            payload={"session_id": str(session_id)},
            priority=2,  # Medium priority for feedback
        )

        return TaskStatusResponse(
            task_id=task_id,
            status="pending",
            task_type="ai_get_feedback",
            session_id=session_id,
            created_at=datetime.utcnow(),
            started_at=None,
            completed_at=None,
            progress=None,
            result=None,
            error=None,
            retry_count=0,
        )

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except Exception as e:
        log_error(logger, e, context="get_ai_feedback_async")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue feedback generation: {str(e)}",
        )


@router.get("/{session_id}/ai/summary/async", response_model=TaskStatusResponse)
async def get_conversation_summary_async(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Get AI-generated conversation summary asynchronously"""
    log_endpoint_call(
        logger,
        f"/async/sessions/{session_id}/ai/summary/async",
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

        # Queue summary generation task
        task_handler = await get_task_websocket_handler()
        task_id = await task_handler.start_task_with_websocket(
            task_type=TaskType.AI_GET_SUMMARY,
            session_id=str(session_id),
            user_id=str(current_user.user_id),
            payload={"session_id": str(session_id)},
            priority=3,  # Low priority for summaries
        )

        return TaskStatusResponse(
            task_id=task_id,
            status="pending",
            task_type="ai_get_summary",
            session_id=session_id,
            created_at=datetime.utcnow(),
            started_at=None,
            completed_at=None,
            progress=None,
            result=None,
            error=None,
            retry_count=0,
        )

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except Exception as e:
        log_error(logger, e, context="get_conversation_summary_async")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue summary generation: {str(e)}",
        )


# Reuse existing synchronous endpoints for quick operations
@router.get("/", response_model=SessionListResponse)
async def get_user_sessions_async(
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: Optional[SessionStatus] = Query(default=None),
):
    """Get user's interview sessions (fast operation, no async needed)"""
    log_endpoint_call(
        logger, "/async/sessions", "GET", user_id=str(current_user.user_id)
    )

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
        log_error(logger, e, context="get_user_sessions_async")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sessions: {str(e)}",
        )


@router.get("/{session_id}/messages", response_model=ConversationHistoryResponse)
async def get_conversation_history_async(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
    limit: Optional[int] = Query(default=None, ge=1, le=500),
):
    """Get conversation history for a session (fast operation, no async needed)"""
    log_endpoint_call(
        logger,
        f"/async/sessions/{session_id}/messages",
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

        from app.interfaces.schemas.session_schemas import MessageResponse

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
        log_error(logger, e, context="get_conversation_history_async")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation: {str(e)}",
        )


# Missing MVP Endpoints - Critical for basic functionality


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_by_id(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Get specific session by ID"""
    log_endpoint_call(
        logger,
        f"/async/sessions/{session_id}",
        "GET",
        user_id=str(current_user.user_id),
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
        log_error(logger, e, context="get_session_by_id")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session: {str(e)}",
        )


@router.put("/{session_id}/status", response_model=SessionResponse)
async def update_session_status(
    session_id: UUID,
    action_request: SessionActionRequest,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Update session status (complete, pause, abandon)"""
    log_endpoint_call(
        logger,
        f"/async/sessions/{session_id}/status",
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

        # Update status using service
        updated_session = await session_service.update_session_status(
            session_id, action_request.action
        )

        return SessionResponse.from_entity(updated_session)

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


@router.get("/{session_id}/metrics", response_model=SessionMetricsResponse)
async def get_session_metrics(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Get session metrics and statistics"""
    log_endpoint_call(
        logger,
        f"/async/sessions/{session_id}/metrics",
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

        # Get session metrics
        metrics = session.get_session_metrics()

        return SessionMetricsResponse(session_id=session_id, metrics=metrics)

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except Exception as e:
        log_error(logger, e, context="get_session_metrics")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session metrics: {str(e)}",
        )


@router.get("/stats/user", response_model=UserSessionStatsResponse)
async def get_user_session_stats(
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Get user's overall session statistics"""
    log_endpoint_call(
        logger, "/async/sessions/stats/user", "GET", user_id=str(current_user.user_id)
    )

    try:
        stats = await session_service.get_user_session_stats(current_user.user_id)

        return UserSessionStatsResponse(user_id=current_user.user_id, stats=stats)

    except Exception as e:
        log_error(logger, e, context="get_user_session_stats")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user stats: {str(e)}",
        )


@router.delete("/{session_id}")
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Delete session (soft delete - for user cleanup)"""
    log_endpoint_call(
        logger,
        f"/async/sessions/{session_id}",
        "DELETE",
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

        # For MVP - only allow deletion of completed/abandoned sessions
        if session.status not in [SessionStatus.COMPLETED, SessionStatus.ABANDONED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only delete completed or abandoned sessions",
            )

        success = await session_service.delete_session(session_id)

        if success:
            return {"message": "Session deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete session",
            )

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    except Exception as e:
        log_error(logger, e, context="delete_session")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}",
        )
