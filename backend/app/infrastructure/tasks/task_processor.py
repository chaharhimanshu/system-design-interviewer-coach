"""
Background Task Processor
Processes AI tasks in the background with progress updates
"""

import asyncio
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

from app.shared.logging import get_logger
from app.infrastructure.tasks.task_queue import (
    TaskManager,
    TaskType,
    TaskStatus,
    Task,
    get_task_manager,
)
from app.infrastructure.tasks.websocket_manager import connection_manager
from app.application.services.ai_service import AIService

logger = get_logger(__name__)


class TaskProcessor:
    """Background task processor for AI operations"""

    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager
        self.ai_service = AIService()
        self.running = False
        self.worker_tasks = []
        self.max_workers = 3  # Number of concurrent workers

    async def start(self):
        """Start the background task processor"""
        if self.running:
            return

        self.running = True
        logger.info(f"Starting task processor with {self.max_workers} workers")

        # Start worker tasks
        for i in range(self.max_workers):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(task)

        logger.info("Task processor started successfully")

    async def stop(self):
        """Stop the background task processor"""
        if not self.running:
            return

        self.running = False
        logger.info("Stopping task processor...")

        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)

        self.worker_tasks.clear()
        logger.info("Task processor stopped")

    async def _worker(self, worker_name: str):
        """Background worker that processes tasks"""
        logger.info(f"Worker {worker_name} started")

        while self.running:
            try:
                # Get next task
                task = await self.task_manager.dequeue_task()

                if task is None:
                    # No tasks available, wait a bit
                    await asyncio.sleep(1)
                    continue

                logger.info(
                    f"Worker {worker_name} processing task {task.task_id} ({task.task_type.value})"
                )

                # Process the task
                await self._process_task(task, worker_name)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait before retrying

        logger.info(f"Worker {worker_name} stopped")

    async def _process_task(self, task: Task, worker_name: str):
        """Process a single task"""

        try:
            # Update progress - starting
            await self._update_progress(
                task.task_id,
                "initializing",
                0,
                4,
                f"Starting {task.task_type.value} processing",
            )

            # Notify WebSocket connections
            await connection_manager.notify_task_update(task)

            # Route to appropriate processor
            if task.task_type == TaskType.AI_PROCESS_RESPONSE:
                result = await self._process_ai_response(task)
            elif task.task_type == TaskType.AI_START_INTERVIEW:
                result = await self._process_ai_start_interview(task)
            elif task.task_type == TaskType.AI_GENERATE_HINT:
                result = await self._process_ai_hint(task)
            elif task.task_type == TaskType.AI_GET_INSIGHTS:
                result = await self._process_ai_insights(task)
            elif task.task_type == TaskType.AI_GET_FEEDBACK:
                result = await self._process_ai_feedback(task)
            elif task.task_type == TaskType.AI_GET_SUMMARY:
                result = await self._process_ai_summary(task)
            elif task.task_type == TaskType.SESSION_CLEANUP:
                result = await self._process_session_cleanup(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")

            # Complete the task
            await self.task_manager.complete_task(task.task_id, result)

            # Update task and notify
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.utcnow()
            await connection_manager.notify_task_update(task)

            logger.info(f"Task {task.task_id} completed successfully by {worker_name}")

        except Exception as e:
            error_msg = f"Task processing failed: {str(e)}"
            logger.error(f"Task {task.task_id} failed: {error_msg}", exc_info=True)

            # Fail the task
            await self.task_manager.fail_task(task.task_id, error_msg)

            # Update task and notify
            task.status = TaskStatus.FAILED
            task.error = error_msg
            task.completed_at = datetime.utcnow()
            await connection_manager.notify_task_update(task)

    async def _update_progress(
        self,
        task_id: str,
        step: str,
        completed: int,
        total: int,
        message: str,
        details: Dict[str, Any] = None,
    ):
        """Update task progress with WebSocket notification"""

        await self.task_manager.update_task_progress(
            task_id=task_id,
            current_step=step,
            completed_steps=completed,
            total_steps=total,
            message=message,
            details=details or {},
        )

        # Get task to find session_id for WebSocket notification
        task = await self.task_manager.get_task(task_id)
        if task:
            progress = await self.task_manager.get_task_progress(task_id)
            if progress:
                await connection_manager.notify_task_progress(
                    task_id, progress, task.session_id
                )

    async def _process_ai_response(self, task: Task) -> Dict[str, Any]:
        """Process AI response generation task"""

        session_id = task.payload.get("session_id")
        user_message = task.payload.get("user_message")
        message_type = task.payload.get("message_type", "answer")

        # Step 1: Initialize AI processing
        await self._update_progress(
            task.task_id, "ai_analysis", 1, 4, "Analyzing user response with AI agents"
        )

        # Process with AI service (this includes the orchestrator with all agents)
        ai_response = await self.ai_service.process_user_response(
            session_id=session_id, user_message=user_message, message_type=message_type
        )

        # Step 2: Processing complete
        await self._update_progress(
            task.task_id, "completed", 4, 4, "AI processing completed successfully"
        )

        return {
            "ai_response": ai_response,
            "processed_at": datetime.utcnow().isoformat(),
        }

    async def _process_ai_start_interview(self, task: Task) -> Dict[str, Any]:
        """Process AI interview start task"""

        session = task.payload.get("session")
        user_context = task.payload.get("user_context", {})

        # Step 1: Initialize
        await self._update_progress(
            task.task_id, "initializing", 1, 3, "Starting AI interview session"
        )

        # Step 2: Generate opening question
        await self._update_progress(
            task.task_id,
            "generating_question",
            2,
            3,
            "Generating personalized opening question",
        )

        ai_response = await self.ai_service.start_interview_session(
            session=session, user_context=user_context
        )

        # Step 3: Complete
        await self._update_progress(
            task.task_id, "completed", 3, 3, "Interview session started successfully"
        )

        return {"ai_response": ai_response, "started_at": datetime.utcnow().isoformat()}

    async def _process_ai_hint(self, task: Task) -> Dict[str, Any]:
        """Process AI hint generation task"""

        session_id = task.payload.get("session_id")
        current_question = task.payload.get("current_question")
        user_context = task.payload.get("user_context", "")

        await self._update_progress(
            task.task_id, "generating_hint", 1, 2, "Generating intelligent hint"
        )

        hint_response = await self.ai_service.request_hint(
            session_id=session_id,
            current_question=current_question,
            user_context=user_context,
        )

        await self._update_progress(
            task.task_id, "completed", 2, 2, "Hint generated successfully"
        )

        return {
            "hint_response": hint_response,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def _process_ai_insights(self, task: Task) -> Dict[str, Any]:
        """Process AI insights generation task"""

        session_id = task.payload.get("session_id")

        await self._update_progress(
            task.task_id,
            "analyzing_session",
            1,
            2,
            "Analyzing session performance and generating insights",
        )

        insights = await self.ai_service.get_session_insights(session_id)

        await self._update_progress(
            task.task_id, "completed", 2, 2, "Session insights generated successfully"
        )

        return {"insights": insights, "generated_at": datetime.utcnow().isoformat()}

    async def _process_ai_feedback(self, task: Task) -> Dict[str, Any]:
        """Process AI feedback generation task"""

        session_id = task.payload.get("session_id")

        await self._update_progress(
            task.task_id,
            "generating_feedback",
            1,
            2,
            "Generating comprehensive AI feedback",
        )

        feedback = await self.ai_service.get_interview_feedback(session_id)

        await self._update_progress(
            task.task_id, "completed", 2, 2, "AI feedback generated successfully"
        )

        return {"feedback": feedback, "generated_at": datetime.utcnow().isoformat()}

    async def _process_ai_summary(self, task: Task) -> Dict[str, Any]:
        """Process AI summary generation task"""

        session_id = task.payload.get("session_id")

        await self._update_progress(
            task.task_id, "generating_summary", 1, 2, "Generating conversation summary"
        )

        summary = await self.ai_service.get_conversation_summary(session_id)

        await self._update_progress(
            task.task_id,
            "completed",
            2,
            2,
            "Conversation summary generated successfully",
        )

        return {"summary": summary, "generated_at": datetime.utcnow().isoformat()}

    async def _process_session_cleanup(self, task: Task) -> Dict[str, Any]:
        """Process session cleanup task"""

        session_id = task.payload.get("session_id")

        await self._update_progress(
            task.task_id, "cleaning_up", 1, 2, "Cleaning up AI session resources"
        )

        await self.ai_service.cleanup_session(session_id)

        await self._update_progress(
            task.task_id, "completed", 2, 2, "Session cleanup completed"
        )

        return {
            "cleaned_up": True,
            "session_id": session_id,
            "completed_at": datetime.utcnow().isoformat(),
        }


# Global task processor instance
_task_processor: Optional[TaskProcessor] = None


async def get_task_processor() -> TaskProcessor:
    """Get or create global task processor instance"""
    global _task_processor

    if _task_processor is None:
        task_manager = await get_task_manager()
        _task_processor = TaskProcessor(task_manager)

    return _task_processor


async def start_task_processor():
    """Start the global task processor"""
    processor = await get_task_processor()
    await processor.start()


async def stop_task_processor():
    """Stop the global task processor"""
    global _task_processor

    if _task_processor:
        await _task_processor.stop()
        _task_processor = None
