"""
Task Queue Configuration and Management
Handles Redis-based task queues with async processing
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import redis.asyncio as redis
from app.shared.logging import get_logger
from app.infrastructure.config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


class TaskStatus(str, Enum):
    """Task status enumeration"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskType(str, Enum):
    """Task type enumeration"""

    AI_PROCESS_RESPONSE = "ai_process_response"
    AI_START_INTERVIEW = "ai_start_interview"
    AI_GENERATE_HINT = "ai_generate_hint"
    AI_GET_INSIGHTS = "ai_get_insights"
    AI_GET_FEEDBACK = "ai_get_feedback"
    AI_GET_SUMMARY = "ai_get_summary"
    SESSION_CLEANUP = "session_cleanup"


@dataclass
class TaskProgress:
    """Task progress information"""

    current_step: str
    total_steps: int
    completed_steps: int
    percentage: float
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class Task:
    """Task data structure"""

    task_id: str
    task_type: TaskType
    status: TaskStatus
    session_id: str
    user_id: str
    payload: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: Optional[TaskProgress] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 1  # 1=high, 2=medium, 3=low

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for Redis storage"""
        data = asdict(self)
        # Handle datetime serialization
        if data["created_at"]:
            data["created_at"] = data["created_at"].isoformat()
        if data["started_at"]:
            data["started_at"] = data["started_at"].isoformat()
        if data["completed_at"]:
            data["completed_at"] = data["completed_at"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create task from dictionary"""
        # Handle datetime deserialization
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("started_at"):
            data["started_at"] = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])

        # Handle progress deserialization
        if data.get("progress") and isinstance(data["progress"], dict):
            data["progress"] = TaskProgress(**data["progress"])

        return cls(**data)


class TaskManager:
    """Redis-based task queue manager with async processing"""

    def __init__(self, redis_url: str = None):
        """Initialize task manager"""
        self.redis_url = redis_url or settings.redis_url
        self.redis_pool: Optional[redis.ConnectionPool] = None
        self.redis_client: Optional[redis.Redis] = None
        self.task_queues = {
            1: "tasks:high_priority",  # High priority queue
            2: "tasks:medium_priority",  # Medium priority queue
            3: "tasks:low_priority",  # Low priority queue
        }
        self.task_storage = "tasks:storage"  # Task data storage
        self.task_status = "tasks:status"  # Task status tracking
        self.task_progress = "tasks:progress"  # Task progress tracking
        self.session_tasks = "tasks:sessions"  # Session -> tasks mapping
        self.user_tasks = "tasks:users"  # User -> tasks mapping

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
            )
            self.redis_client = redis.Redis(connection_pool=self.redis_pool)

            # Test connection
            await self.redis_client.ping()
            logger.info("Task manager initialized successfully with Redis")

        except Exception as e:
            logger.error(f"Failed to initialize task manager: {e}")
            raise

    async def cleanup(self):
        """Cleanup Redis connections"""
        if self.redis_client:
            await self.redis_client.close()
        if self.redis_pool:
            await self.redis_pool.disconnect()

    @asynccontextmanager
    async def get_redis(self):
        """Get Redis client with connection management"""
        if not self.redis_client:
            await self.initialize()
        try:
            yield self.redis_client
        except Exception as e:
            logger.error(f"Redis operation failed: {e}")
            raise

    async def enqueue_task(
        self,
        task_type: TaskType,
        session_id: str,
        user_id: str,
        payload: Dict[str, Any],
        priority: int = 2,
        max_retries: int = 3,
    ) -> str:
        """Enqueue a new task for processing"""

        task_id = str(uuid.uuid4())
        task = Task(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            session_id=session_id,
            user_id=user_id,
            payload=payload,
            priority=priority,
            max_retries=max_retries,
        )

        async with self.get_redis() as redis_client:
            # Store task data
            await redis_client.hset(
                self.task_storage, task_id, json.dumps(task.to_dict())
            )

            # Add to appropriate priority queue
            queue_name = self.task_queues.get(priority, self.task_queues[2])
            await redis_client.lpush(queue_name, task_id)

            # Update session and user mappings
            await redis_client.sadd(f"{self.session_tasks}:{session_id}", task_id)
            await redis_client.sadd(f"{self.user_tasks}:{user_id}", task_id)

            # Set task status
            await redis_client.hset(self.task_status, task_id, TaskStatus.PENDING.value)

            # Set expiration (24 hours)
            await redis_client.expire(f"{self.session_tasks}:{session_id}", 86400)
            await redis_client.expire(f"{self.user_tasks}:{user_id}", 86400)

        logger.info(f"Task {task_id} enqueued with priority {priority}")
        return task_id

    async def dequeue_task(self, priority_order: List[int] = None) -> Optional[Task]:
        """Dequeue next available task based on priority"""

        if priority_order is None:
            priority_order = [1, 2, 3]  # High to low priority

        async with self.get_redis() as redis_client:
            for priority in priority_order:
                queue_name = self.task_queues.get(priority)
                if not queue_name:
                    continue

                # Try to get task from queue
                task_id = await redis_client.rpop(queue_name)
                if task_id:
                    # Get task data
                    task_data = await redis_client.hget(self.task_storage, task_id)
                    if task_data:
                        task_dict = json.loads(task_data)
                        task = Task.from_dict(task_dict)

                        # Update status to processing
                        task.status = TaskStatus.PROCESSING
                        task.started_at = datetime.utcnow()

                        await self.update_task(task)
                        return task

        return None

    async def update_task(self, task: Task):
        """Update task data in storage"""

        async with self.get_redis() as redis_client:
            # Update task data
            await redis_client.hset(
                self.task_storage, task.task_id, json.dumps(task.to_dict())
            )

            # Update status
            await redis_client.hset(self.task_status, task.task_id, task.status.value)

            # Update progress if available
            if task.progress:
                await redis_client.hset(
                    self.task_progress, task.task_id, json.dumps(asdict(task.progress))
                )

    async def complete_task(
        self,
        task_id: str,
        result: Dict[str, Any],
        status: TaskStatus = TaskStatus.COMPLETED,
    ):
        """Mark task as completed with result"""

        async with self.get_redis() as redis_client:
            task_data = await redis_client.hget(self.task_storage, task_id)
            if task_data:
                task_dict = json.loads(task_data)
                task = Task.from_dict(task_dict)

                task.status = status
                task.result = result
                task.completed_at = datetime.utcnow()

                await self.update_task(task)
                logger.info(f"Task {task_id} completed successfully")

    async def fail_task(self, task_id: str, error: str, retry: bool = True):
        """Mark task as failed with error details"""

        async with self.get_redis() as redis_client:
            task_data = await redis_client.hget(self.task_storage, task_id)
            if task_data:
                task_dict = json.loads(task_data)
                task = Task.from_dict(task_dict)

                task.error = error
                task.retry_count += 1

                if retry and task.retry_count <= task.max_retries:
                    # Re-enqueue for retry
                    task.status = TaskStatus.RETRYING
                    await self.update_task(task)

                    queue_name = self.task_queues.get(
                        task.priority, self.task_queues[2]
                    )
                    await redis_client.lpush(queue_name, task_id)

                    logger.info(
                        f"Task {task_id} queued for retry (attempt {task.retry_count})"
                    )
                else:
                    # Mark as failed
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.utcnow()
                    await self.update_task(task)

                    logger.error(f"Task {task_id} failed permanently: {error}")

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""

        async with self.get_redis() as redis_client:
            task_data = await redis_client.hget(self.task_storage, task_id)
            if task_data:
                task_dict = json.loads(task_data)
                return Task.from_dict(task_dict)
        return None

    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status"""

        async with self.get_redis() as redis_client:
            status = await redis_client.hget(self.task_status, task_id)
            return TaskStatus(status) if status else None

    async def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Get task progress"""

        async with self.get_redis() as redis_client:
            progress_data = await redis_client.hget(self.task_progress, task_id)
            if progress_data:
                progress_dict = json.loads(progress_data)
                return TaskProgress(**progress_dict)
        return None

    async def update_task_progress(
        self,
        task_id: str,
        current_step: str,
        completed_steps: int,
        total_steps: int,
        message: str,
        details: Dict[str, Any] = None,
    ):
        """Update task progress"""

        percentage = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
        progress = TaskProgress(
            current_step=current_step,
            total_steps=total_steps,
            completed_steps=completed_steps,
            percentage=percentage,
            message=message,
            details=details or {},
        )

        async with self.get_redis() as redis_client:
            # Update progress
            await redis_client.hset(
                self.task_progress, task_id, json.dumps(asdict(progress))
            )

            # Also update the task itself
            task = await self.get_task(task_id)
            if task:
                task.progress = progress
                await self.update_task(task)

    async def get_session_tasks(self, session_id: str) -> List[str]:
        """Get all task IDs for a session"""

        async with self.get_redis() as redis_client:
            task_ids = await redis_client.smembers(f"{self.session_tasks}:{session_id}")
            return list(task_ids) if task_ids else []

    async def get_user_tasks(self, user_id: str) -> List[str]:
        """Get all task IDs for a user"""

        async with self.get_redis() as redis_client:
            task_ids = await redis_client.smembers(f"{self.user_tasks}:{user_id}")
            return list(task_ids) if task_ids else []

    async def cancel_task(self, task_id: str):
        """Cancel a pending task"""

        async with self.get_redis() as redis_client:
            task = await self.get_task(task_id)
            if task and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.utcnow()
                await self.update_task(task)

                # Remove from queues
                for queue in self.task_queues.values():
                    await redis_client.lrem(queue, 0, task_id)

                logger.info(f"Task {task_id} cancelled")
                return True
        return False

    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed/failed tasks"""

        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

        async with self.get_redis() as redis_client:
            # Get all task IDs
            task_ids = await redis_client.hkeys(self.task_storage)

            cleaned_count = 0
            for task_id in task_ids:
                task = await self.get_task(task_id)
                if (
                    task
                    and task.completed_at
                    and task.completed_at < cutoff_time
                    and task.status
                    in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                ):

                    # Remove task data
                    await redis_client.hdel(self.task_storage, task_id)
                    await redis_client.hdel(self.task_status, task_id)
                    await redis_client.hdel(self.task_progress, task_id)

                    # Remove from session/user mappings
                    await redis_client.srem(
                        f"{self.session_tasks}:{task.session_id}", task_id
                    )
                    await redis_client.srem(
                        f"{self.user_tasks}:{task.user_id}", task_id
                    )

                    cleaned_count += 1

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old tasks")

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""

        async with self.get_redis() as redis_client:
            stats = {}

            # Queue lengths
            for priority, queue_name in self.task_queues.items():
                length = await redis_client.llen(queue_name)
                stats[f"queue_priority_{priority}"] = length

            # Total tasks by status
            all_task_ids = await redis_client.hkeys(self.task_storage)
            status_counts = {}

            for task_id in all_task_ids:
                status = await redis_client.hget(self.task_status, task_id)
                if status:
                    status_counts[status] = status_counts.get(status, 0) + 1

            stats["status_counts"] = status_counts
            stats["total_tasks"] = len(all_task_ids)

            return stats


# Global task manager instance
_task_manager: Optional[TaskManager] = None


async def get_task_manager() -> TaskManager:
    """Get or create global task manager instance"""
    global _task_manager

    if _task_manager is None:
        _task_manager = TaskManager()
        await _task_manager.initialize()

    return _task_manager


async def cleanup_task_manager():
    """Cleanup global task manager"""
    global _task_manager

    if _task_manager:
        await _task_manager.cleanup()
        _task_manager = None
