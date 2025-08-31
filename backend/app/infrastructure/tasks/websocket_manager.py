"""
WebSocket Connection Manager
Handles real-time WebSocket connections for live updates during AI processing
"""

import json
import asyncio
from typing import Dict, Set, Optional, Any, List
from datetime import datetime
from uuid import UUID
from contextlib import asynccontextmanager

from fastapi import WebSocket, WebSocketDisconnect, status
from app.shared.logging import get_logger
from app.infrastructure.tasks.task_queue import (
    TaskManager,
    TaskStatus,
    Task,
    TaskProgress,
)

logger = get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        # Active connections by session_id
        self.session_connections: Dict[str, Set[WebSocket]] = {}

        # Active connections by user_id
        self.user_connections: Dict[str, Set[WebSocket]] = {}

        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

        # Task subscriptions (websocket -> task_ids)
        self.task_subscriptions: Dict[WebSocket, Set[str]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: str,
        connection_type: str = "session",
    ):
        """Accept WebSocket connection and register it"""

        await websocket.accept()

        # Store connection metadata
        self.connection_metadata[websocket] = {
            "session_id": session_id,
            "user_id": user_id,
            "connection_type": connection_type,
            "connected_at": datetime.utcnow(),
        }

        # Add to session connections
        if session_id not in self.session_connections:
            self.session_connections[session_id] = set()
        self.session_connections[session_id].add(websocket)

        # Add to user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)

        # Initialize task subscriptions
        self.task_subscriptions[websocket] = set()

        logger.info(
            f"WebSocket connected - Session: {session_id}, User: {user_id}, Type: {connection_type}"
        )

        # Send welcome message
        await self.send_to_connection(
            websocket,
            {
                "type": "connection_established",
                "message": "WebSocket connection established",
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""

        if websocket not in self.connection_metadata:
            return

        metadata = self.connection_metadata[websocket]
        session_id = metadata["session_id"]
        user_id = metadata["user_id"]

        # Remove from session connections
        if session_id in self.session_connections:
            self.session_connections[session_id].discard(websocket)
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]

        # Remove from user connections
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        # Clean up subscriptions
        if websocket in self.task_subscriptions:
            del self.task_subscriptions[websocket]

        # Remove metadata
        del self.connection_metadata[websocket]

        logger.info(f"WebSocket disconnected - Session: {session_id}, User: {user_id}")

    async def send_to_connection(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific WebSocket connection"""

        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            await self.disconnect(websocket)

    async def send_to_session(self, session_id: str, message: Dict[str, Any]):
        """Send message to all connections for a session"""

        if session_id not in self.session_connections:
            return

        disconnected_connections = []

        for websocket in self.session_connections[session_id].copy():
            try:
                await websocket.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.error(f"Failed to send message to session {session_id}: {e}")
                disconnected_connections.append(websocket)

        # Clean up disconnected connections
        for websocket in disconnected_connections:
            await self.disconnect(websocket)

    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to all connections for a user"""

        if user_id not in self.user_connections:
            return

        disconnected_connections = []

        for websocket in self.user_connections[user_id].copy():
            try:
                await websocket.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                disconnected_connections.append(websocket)

        # Clean up disconnected connections
        for websocket in disconnected_connections:
            await self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connections"""

        all_connections = set()
        for connections in self.session_connections.values():
            all_connections.update(connections)

        disconnected_connections = []

        for websocket in all_connections:
            try:
                await websocket.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.error(f"Failed to broadcast message: {e}")
                disconnected_connections.append(websocket)

        # Clean up disconnected connections
        for websocket in disconnected_connections:
            await self.disconnect(websocket)

    def subscribe_to_task(self, websocket: WebSocket, task_id: str):
        """Subscribe WebSocket to task updates"""

        if websocket in self.task_subscriptions:
            self.task_subscriptions[websocket].add(task_id)
            logger.info(f"WebSocket subscribed to task {task_id}")

    def unsubscribe_from_task(self, websocket: WebSocket, task_id: str):
        """Unsubscribe WebSocket from task updates"""

        if websocket in self.task_subscriptions:
            self.task_subscriptions[websocket].discard(task_id)
            logger.info(f"WebSocket unsubscribed from task {task_id}")

    async def notify_task_update(self, task: Task):
        """Notify all subscribed connections about task update"""

        message = {
            "type": "task_update",
            "task_id": task.task_id,
            "status": task.status.value,
            "session_id": task.session_id,
            "user_id": task.user_id,
            "task_type": task.task_type.value,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Add progress if available
        if task.progress:
            message["progress"] = {
                "current_step": task.progress.current_step,
                "completed_steps": task.progress.completed_steps,
                "total_steps": task.progress.total_steps,
                "percentage": task.progress.percentage,
                "message": task.progress.message,
                "details": task.progress.details,
            }

        # Add result if completed
        if task.status == TaskStatus.COMPLETED and task.result:
            message["result"] = task.result

        # Add error if failed
        if task.status == TaskStatus.FAILED and task.error:
            message["error"] = task.error

        # Send to subscribed connections
        for websocket, task_ids in self.task_subscriptions.items():
            if task.task_id in task_ids:
                await self.send_to_connection(websocket, message)

        # Also send to session connections
        await self.send_to_session(task.session_id, message)

    async def notify_task_progress(
        self, task_id: str, progress: TaskProgress, session_id: str
    ):
        """Notify about task progress update"""

        message = {
            "type": "task_progress",
            "task_id": task_id,
            "session_id": session_id,
            "progress": {
                "current_step": progress.current_step,
                "completed_steps": progress.completed_steps,
                "total_steps": progress.total_steps,
                "percentage": progress.percentage,
                "message": progress.message,
                "details": progress.details,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Send to subscribed connections
        for websocket, task_ids in self.task_subscriptions.items():
            if task_id in task_ids:
                await self.send_to_connection(websocket, message)

        # Also send to session connections
        await self.send_to_session(session_id, message)

    async def handle_client_message(
        self, websocket: WebSocket, message: Dict[str, Any]
    ):
        """Handle incoming client messages"""

        message_type = message.get("type")

        if message_type == "subscribe_task":
            task_id = message.get("task_id")
            if task_id:
                self.subscribe_to_task(websocket, task_id)
                await self.send_to_connection(
                    websocket,
                    {
                        "type": "subscription_confirmed",
                        "task_id": task_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

        elif message_type == "unsubscribe_task":
            task_id = message.get("task_id")
            if task_id:
                self.unsubscribe_from_task(websocket, task_id)
                await self.send_to_connection(
                    websocket,
                    {
                        "type": "unsubscription_confirmed",
                        "task_id": task_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

        elif message_type == "ping":
            await self.send_to_connection(
                websocket, {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
            )

        else:
            await self.send_to_connection(
                websocket,
                {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""

        return {
            "total_connections": sum(
                len(connections) for connections in self.session_connections.values()
            ),
            "active_sessions": len(self.session_connections),
            "active_users": len(self.user_connections),
            "task_subscriptions": sum(
                len(tasks) for tasks in self.task_subscriptions.values()
            ),
        }

    async def cleanup_inactive_connections(self):
        """Clean up inactive WebSocket connections"""

        inactive_connections = []

        for websocket in list(self.connection_metadata.keys()):
            try:
                # Send ping to check if connection is alive
                await websocket.send_text(json.dumps({"type": "ping"}))
            except:
                inactive_connections.append(websocket)

        for websocket in inactive_connections:
            await self.disconnect(websocket)

        if inactive_connections:
            logger.info(
                f"Cleaned up {len(inactive_connections)} inactive WebSocket connections"
            )


# Global connection manager instance
connection_manager = ConnectionManager()


# WebSocket event handlers for task processing
class TaskWebSocketHandler:
    """Handles WebSocket events for task processing"""

    def __init__(
        self, connection_manager: ConnectionManager, task_manager: TaskManager
    ):
        self.connection_manager = connection_manager
        self.task_manager = task_manager

    async def start_task_with_websocket(
        self,
        task_type: str,
        session_id: str,
        user_id: str,
        payload: Dict[str, Any],
        priority: int = 2,
    ) -> str:
        """Start a task and automatically set up WebSocket notifications"""

        task_id = await self.task_manager.enqueue_task(
            task_type=task_type,
            session_id=session_id,
            user_id=user_id,
            payload=payload,
            priority=priority,
        )

        # Notify via WebSocket
        await self.connection_manager.send_to_session(
            session_id,
            {
                "type": "task_started",
                "task_id": task_id,
                "task_type": task_type,
                "status": "pending",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return task_id

    async def update_task_progress_with_websocket(
        self,
        task_id: str,
        current_step: str,
        completed_steps: int,
        total_steps: int,
        message: str,
        details: Dict[str, Any] = None,
    ):
        """Update task progress and notify via WebSocket"""

        await self.task_manager.update_task_progress(
            task_id=task_id,
            current_step=current_step,
            completed_steps=completed_steps,
            total_steps=total_steps,
            message=message,
            details=details,
        )

        # Get task to find session_id
        task = await self.task_manager.get_task(task_id)
        if task:
            progress = await self.task_manager.get_task_progress(task_id)
            if progress:
                await self.connection_manager.notify_task_progress(
                    task_id, progress, task.session_id
                )


# Global task WebSocket handler
task_websocket_handler: Optional[TaskWebSocketHandler] = None


async def get_task_websocket_handler() -> TaskWebSocketHandler:
    """Get or create global task WebSocket handler"""
    global task_websocket_handler

    if task_websocket_handler is None:
        from app.infrastructure.tasks.task_queue import get_task_manager

        task_manager = await get_task_manager()
        task_websocket_handler = TaskWebSocketHandler(connection_manager, task_manager)

    return task_websocket_handler
