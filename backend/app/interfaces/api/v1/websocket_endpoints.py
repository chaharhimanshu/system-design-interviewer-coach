"""
WebSocket API Endpoints
Real-time WebSocket connections for task updates and live session monitoring
"""

import json
from typing import Dict, Any
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    HTTPException,
    status,
)
from uuid import UUID

from app.shared.logging import get_logger, log_endpoint_call
from app.infrastructure.tasks.websocket_manager import (
    connection_manager,
    get_task_websocket_handler,
)
from app.infrastructure.tasks.task_queue import get_task_manager
from app.interfaces.api.v1.user_endpoints import get_current_user_ws
from app.domain.entities.user import User
from app.application.services.session_service import SessionService
from app.infrastructure.database.repositories.session_repository_impl import (
    PostgreSQLSessionRepository,
)
from app.infrastructure.database.repositories.user_repository_impl import (
    PostgreSQLUserRepository,
)
from app.infrastructure.database.config import get_db_session

logger = get_logger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])


async def get_session_service_ws(db=None) -> SessionService:
    """Get session service for WebSocket connections"""
    if db is None:
        # For WebSocket we need to get db differently
        from app.infrastructure.database.config import db_config

        db = db_config.get_session()

    session_repository = PostgreSQLSessionRepository(db)
    user_repository = PostgreSQLUserRepository(db)
    return SessionService(session_repository, user_repository)


@router.websocket("/session/{session_id}")
async def websocket_session_endpoint(
    websocket: WebSocket, session_id: UUID, token: str = None
):
    """WebSocket endpoint for real-time session updates"""

    try:
        # Authenticate user
        current_user = await get_current_user_ws(token)
        if not current_user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Verify session access
        session_service = await get_session_service_ws()
        session = await session_service.get_session(session_id)

        if session.user_id != current_user.user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Connect to WebSocket manager
        await connection_manager.connect(
            websocket=websocket,
            session_id=str(session_id),
            user_id=str(current_user.user_id),
            connection_type="session",
        )

        logger.info(
            f"WebSocket session connection established - Session: {session_id}, User: {current_user.user_id}"
        )

        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                await connection_manager.handle_client_message(websocket, message)

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await connection_manager.send_to_connection(
                    websocket,
                    {
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": None,
                    },
                )
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
                await connection_manager.send_to_connection(
                    websocket,
                    {
                        "type": "error",
                        "message": "Internal server error",
                        "timestamp": None,
                    },
                )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        await connection_manager.disconnect(websocket)


@router.websocket("/user/{user_id}")
async def websocket_user_endpoint(
    websocket: WebSocket, user_id: UUID, token: str = None
):
    """WebSocket endpoint for user-wide updates"""

    try:
        # Authenticate user
        current_user = await get_current_user_ws(token)
        if not current_user or current_user.user_id != user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Connect to WebSocket manager
        await connection_manager.connect(
            websocket=websocket,
            session_id="",  # User-wide connection
            user_id=str(user_id),
            connection_type="user",
        )

        logger.info(f"WebSocket user connection established - User: {user_id}")

        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                await connection_manager.handle_client_message(websocket, message)

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await connection_manager.send_to_connection(
                    websocket,
                    {
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": None,
                    },
                )
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
                await connection_manager.send_to_connection(
                    websocket,
                    {
                        "type": "error",
                        "message": "Internal server error",
                        "timestamp": None,
                    },
                )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        await connection_manager.disconnect(websocket)


# REST endpoints for WebSocket management
@router.get("/connections/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""

    stats = connection_manager.get_connection_stats()
    return {"status": "healthy", "stats": stats}


@router.post("/connections/cleanup")
async def cleanup_websocket_connections():
    """Clean up inactive WebSocket connections"""

    await connection_manager.cleanup_inactive_connections()
    return {"status": "success", "message": "Inactive connections cleaned up"}


@router.get("/tasks/stats")
async def get_task_stats():
    """Get task queue statistics"""

    task_manager = await get_task_manager()
    stats = await task_manager.get_queue_stats()

    return {"status": "healthy", "stats": stats}


@router.post("/tasks/cleanup")
async def cleanup_old_tasks():
    """Clean up old completed tasks"""

    task_manager = await get_task_manager()
    await task_manager.cleanup_old_tasks()

    return {"status": "success", "message": "Old tasks cleaned up"}
