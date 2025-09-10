"""
Database-Backed Memory Manager with Sliding Window
Manages conversation memory using PostgreSQL with smart context retrieval
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
import logging
import json

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from sqlalchemy import text

from app.agents.models.output_schemas import MemoryEnhancedInterviewState
from app.infrastructure.config.settings import get_settings
from app.domain.repositories.session_repository import ISessionRepository
from app.shared.logging import get_logger

logger = get_logger(__name__)


class MemoryEnhancedSessionManager:
    """
    Session manager focused on memory and state management.

    Core Responsibilities:
    - Track session state and metadata
    - Provide sliding window conversation context
    - Manage conversation flow and transitions
    - Interface with database for message persistence
    """

    def __init__(
        self,
        max_recent_messages: int = 10,
        session_repository: Optional[ISessionRepository] = None,
    ):
        # Add instance tracking for debugging
        self.instance_id = datetime.utcnow().isoformat()
        self.max_recent_messages = max_recent_messages
        self.settings = get_settings()
        self.session_repository = session_repository

        # Track active sessions in memory for quick access
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        logger.info(
            f"MemoryEnhancedSessionManager initialized - instance: {self.instance_id}, "
            f"sliding_window_size: {max_recent_messages}"
        )

    @property
    def sliding_window_size(self) -> int:
        """Get the sliding window size for conversation messages."""
        return self.max_recent_messages

    def get_config(self, session_id: str) -> Dict[str, Any]:
        """
        Get LangGraph config for a session.
        All agents using this config will share the same memory thread.

        Args:
            session_id: Session identifier

        Returns:
            LangGraph configuration for memory sharing
        """
        return {"configurable": {"thread_id": session_id}}

    def get_memory_saver(self):
        """
        Return None for checkpointer since we use database memory.
        This allows create_react_agent to work without LangGraph memory.
        """
        return None

    async def initialize_session(
        self,
        session_id: str,
        topic: str,
        difficulty: str,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> MemoryEnhancedInterviewState:
        """
        Initialize a new session with enhanced state and comprehensive logging.

        Args:
            session_id: Unique session identifier
            topic: Interview topic
            difficulty: Difficulty level
            user_context: Additional user context

        Returns:
            Initial enhanced state
        """
        logger.info(
            f"Initializing session with database memory strategy",
            extra={
                "session_id": session_id,
                "topic": topic,
                "difficulty": difficulty,
                "has_user_context": bool(user_context),
                "memory_manager_instance": self.instance_id,
                "sliding_window_size": self.max_recent_messages,
            },
        )

        # Create initial state
        initial_state = MemoryEnhancedInterviewState(
            interview_session_id=session_id,
            current_topic=topic,
            difficulty_level=difficulty,
            interview_phase="opening",
            question_count=0,
            user_performance={},
            evaluation_history=[],
            follow_up_context="",
            ready_for_summary=False,
            session_complete=False,
        )

        # Store session metadata with message storage
        session_metadata = {
            "topic": topic,
            "difficulty": difficulty,
            "start_time": datetime.utcnow(),
            "user_context": user_context or {},
            "state": initial_state,
            "messages": [],  # Add message storage to session
        }

        self.active_sessions[session_id] = session_metadata

        # Log session creation with detailed metadata
        logger.info(
            f"Session initialized successfully",
            extra={
                "session_id": session_id,
                "topic": topic,
                "difficulty": difficulty,
                "initial_phase": initial_state.interview_phase,
                "session_metadata_keys": list(session_metadata.keys()),
                "active_sessions_count": len(self.active_sessions),
                "memory_strategy": "database_sliding_window",
            },
        )

        return initial_state

    async def add_answer_to_memory(
        self,
        session_id: str,
        answer: str,
        answer_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Store user answer in session state with comprehensive logging.

        Args:
            session_id: Session identifier
            answer: User's answer
            answer_context: Additional context about the answer
        """
        if session_id not in self.active_sessions:
            logger.warning(
                f"Session not found in active sessions",
                extra={
                    "session_id": session_id,
                    "active_sessions": list(self.active_sessions.keys()),
                    "active_sessions_count": len(self.active_sessions),
                    "action": "add_answer_to_memory",
                },
            )
            return

        # Store answer in session state for agent access
        session_data = self.active_sessions[session_id]
        if "state" in session_data:
            session_data["state"].last_user_answer = answer
            session_data["state"].last_answer_context = answer_context or {}

        logger.info(
            f"User answer stored in session state",
            extra={
                "session_id": session_id,
                "answer_length": len(answer),
                "answer_preview": answer[:100] + "..." if len(answer) > 100 else answer,
                "context_keys": list(answer_context.keys()) if answer_context else [],
                "has_context": bool(answer_context),
                "memory_action": "answer_stored",
            },
        )

    async def add_evaluation_to_memory(
        self, session_id: str, evaluation: Dict[str, Any]
    ):
        """
        Add evaluation results to session memory with detailed logging.

        Args:
            session_id: Session identifier
            evaluation: Evaluation results
        """
        if session_id not in self.active_sessions:
            logger.warning(
                f"Session not found for evaluation storage",
                extra={
                    "session_id": session_id,
                    "active_sessions": list(self.active_sessions.keys()),
                    "evaluation_keys": list(evaluation.keys()) if evaluation else [],
                    "action": "add_evaluation_to_memory",
                },
            )
            return

        # Update session state
        session_data = self.active_sessions[session_id]
        if "state" in session_data:
            session_data["state"].evaluation_history.append(evaluation)
            evaluation_count = len(session_data["state"].evaluation_history)
        else:
            evaluation_count = 0

        logger.info(
            f"Evaluation added to session memory",
            extra={
                "session_id": session_id,
                "evaluation_keys": list(evaluation.keys()) if evaluation else [],
                "total_evaluations": evaluation_count,
                "overall_score": evaluation.get("overall_score", "N/A"),
                "evaluation_type": evaluation.get("type", "unknown"),
                "memory_action": "evaluation_stored",
            },
        )

    async def update_session_state(
        self, session_id: str, state_updates: Dict[str, Any]
    ):
        """
        Update session state with comprehensive change tracking.

        Args:
            session_id: Session identifier
            state_updates: State updates to apply
        """
        if session_id not in self.active_sessions:
            logger.warning(
                f"Session not found for state update",
                extra={
                    "session_id": session_id,
                    "active_sessions": list(self.active_sessions.keys()),
                    "update_keys": list(state_updates.keys()),
                    "action": "update_session_state",
                },
            )
            return

        session_data = self.active_sessions[session_id]
        updated_fields = []

        if "state" in session_data:
            # Track what gets updated
            for key, new_value in state_updates.items():
                if hasattr(session_data["state"], key):
                    old_value = getattr(session_data["state"], key, None)
                    setattr(session_data["state"], key, new_value)
                    updated_fields.append(
                        {
                            "field": key,
                            "old_value": str(old_value)[:50] if old_value else None,
                            "new_value": str(new_value)[:50] if new_value else None,
                        }
                    )

        logger.info(
            f"Session state updated",
            extra={
                "session_id": session_id,
                "updated_fields": updated_fields,
                "total_updates": len(updated_fields),
                "update_keys": list(state_updates.keys()),
                "memory_action": "state_updated",
            },
        )

    async def get_session_state(
        self, session_id: str
    ) -> Optional[MemoryEnhancedInterviewState]:
        """
        Get current session state.

        Args:
            session_id: Session identifier

        Returns:
            Current session state or None if not found
        """
        if session_id not in self.active_sessions:
            return None

        return self.active_sessions[session_id].get("state")

    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get comprehensive session summary.

        Args:
            session_id: Session identifier

        Returns:
            Session summary with metadata and performance
        """
        if session_id not in self.active_sessions:
            return {"error": f"Session {session_id} not found"}

        session_data = self.active_sessions[session_id]
        state = session_data.get("state")

        if not state:
            return {"error": f"No state found for session {session_id}"}

        # Calculate performance metrics
        avg_score = 0
        if state.evaluation_history:
            scores = [
                eval.get("scores", {}).get("average_score", 0)
                for eval in state.evaluation_history
            ]
            avg_score = sum(scores) / len(scores) if scores else 0

        summary = {
            "session_id": session_id,
            "topic": state.current_topic,
            "difficulty": state.difficulty_level,
            "phase": state.interview_phase,
            "questions_asked": state.question_count,
            "evaluations_count": len(state.evaluation_history),
            "average_score": avg_score,
            "ready_for_summary": state.ready_for_summary,
            "session_complete": state.session_complete,
            "start_time": (
                session_data.get("start_time", "").isoformat()
                if session_data.get("start_time")
                else ""
            ),
            "memory_config": self.get_config(session_id),
        }

        return summary

    async def should_generate_summary(self, session_id: str) -> bool:
        """
        Determine if session is ready for summary generation.

        Args:
            session_id: Session identifier

        Returns:
            True if ready for summary
        """
        state = await self.get_session_state(session_id)
        if not state:
            return False

        # Summary conditions from the architecture document
        return (
            state.question_count >= 5
            and len(state.evaluation_history) >= 3
            and not state.ready_for_summary  # Haven't generated summary yet
        )

    async def cleanup_session(self, session_id: str):
        """
        Clean up session resources.

        Args:
            session_id: Session identifier to clean up
        """
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Cleaned up session {session_id}")

        # Note: LangGraph MemorySaver handles its own cleanup
        # We could optionally clear specific thread memory here if needed

    async def get_session_metrics(self) -> Dict[str, Any]:
        """Get comprehensive session metrics with detailed logging."""
        metrics = {
            "total_active_sessions": len(self.active_sessions),
            "memory_type": "database_sliding_window",
            "max_recent_messages": self.max_recent_messages,
            "instance_id": self.instance_id,
            "sessions": list(self.active_sessions.keys()),
            "session_details": {},
        }

        # Add detailed session information
        for session_id, session_data in self.active_sessions.items():
            state = session_data.get("state")
            metrics["session_details"][session_id] = {
                "topic": session_data.get("topic", "unknown"),
                "difficulty": session_data.get("difficulty", "unknown"),
                "start_time": (
                    session_data.get("start_time", "").isoformat()
                    if session_data.get("start_time")
                    else ""
                ),
                "question_count": getattr(state, "question_count", 0) if state else 0,
                "evaluation_count": (
                    len(getattr(state, "evaluation_history", [])) if state else 0
                ),
                "current_phase": (
                    getattr(state, "interview_phase", "unknown") if state else "unknown"
                ),
            }

        logger.debug(
            f"Session metrics retrieved",
            extra={
                "active_sessions_count": metrics["total_active_sessions"],
                "memory_strategy": metrics["memory_type"],
                "sliding_window_size": metrics["max_recent_messages"],
                "instance_id": self.instance_id,
            },
        )

        return metrics

    async def get_memory_contents(self, session_id: str) -> Dict[str, Any]:
        """
        Get the actual memory contents from database for debugging.

        Args:
            session_id: Session identifier

        Returns:
            Memory contents including all messages and state
        """
        try:
            # TODO: Implement actual database memory retrieval when available
            # For now, return placeholder data based on active sessions

            session_in_active = session_id in self.active_sessions
            state = (
                self.active_sessions.get(session_id, {}).get("state")
                if session_in_active
                else None
            )

            return {
                "session_id": session_id,
                "memory_status": "placeholder_active",
                "memory_type": "sliding_window_placeholder",
                "sliding_window_size": self.max_recent_messages,
                "total_messages_in_db": 0,  # Will be actual count when implemented
                "messages_in_window": 0,  # Will be actual count when implemented
                "conversation_messages": [],  # Will be actual messages when implemented
                "session_state": (
                    {
                        "interview_session_id": getattr(
                            state, "interview_session_id", None
                        ),
                        "current_topic": getattr(state, "current_topic", None),
                        "difficulty_level": getattr(state, "difficulty_level", None),
                        "interview_phase": getattr(state, "interview_phase", None),
                        "question_count": getattr(state, "question_count", 0),
                        "evaluation_history_count": len(
                            getattr(state, "evaluation_history", [])
                        ),
                        "user_performance": getattr(state, "user_performance", None),
                    }
                    if state
                    else None
                ),
            }

        except Exception as e:
            logger.error(f"Error getting memory contents for session {session_id}: {e}")
            return {
                "session_id": session_id,
                "memory_status": "error",
                "error": str(e),
                "database_connection": "failed",
            }

    async def list_all_memory_threads(self) -> Dict[str, Any]:
        """
        List all memory threads stored in the database.
        Useful for debugging what's actually stored in memory.
        """
        try:
            # Get all active sessions and their memory contents
            active_threads = []

            for session_id in self.active_sessions.keys():
                memory_contents = await self.get_memory_contents(session_id)
                active_threads.append(
                    {
                        "session_id": session_id,
                        "memory_status": memory_contents["memory_status"],
                        "total_messages_in_db": memory_contents.get(
                            "total_messages_in_db", 0
                        ),
                        "messages_in_window": memory_contents.get(
                            "messages_in_window", 0
                        ),
                        "session_state_exists": memory_contents.get("session_state")
                        is not None,
                    }
                )

            # Get total database stats - placeholder implementation
            total_sessions_with_messages = len(self.active_sessions)
            total_messages = 0  # Will be actual count when implemented

            return {
                "memory_type": "sliding_window_placeholder",
                "sliding_window_size": self.max_recent_messages,
                "active_sessions_in_memory": len(active_threads),
                "total_sessions_with_messages": total_sessions_with_messages,
                "total_messages_in_database": total_messages,
                "active_threads": active_threads,
            }

        except Exception as e:
            logger.error(f"Error listing memory threads: {e}")
            return {
                "error": str(e),
                "memory_type": "database_sliding_window",
                "database_connection": "failed",
            }

    async def get_conversation_messages(self, session_id: str) -> List[BaseMessage]:
        """
        Get recent conversation messages using sliding window strategy.

        Args:
            session_id: Session identifier

        Returns:
            List of recent messages (limited by max_recent_messages)
        """
        logger.debug(
            f"Retrieving conversation messages for session {session_id} with sliding window size: {self.max_recent_messages}"
        )

        try:
            # Get messages from active session storage
            if session_id in self.active_sessions:
                messages = self.active_sessions[session_id].get("messages", [])
                # Apply sliding window (get most recent messages)
                recent_messages = (
                    messages[-self.max_recent_messages :] if messages else []
                )

                logger.info(
                    f"Conversation messages retrieved for session {session_id}",
                    extra={
                        "session_id": session_id,
                        "window_size": self.max_recent_messages,
                        "messages_found": len(recent_messages),
                        "total_messages": len(messages),
                        "memory_strategy": "sliding_window",
                    },
                )

                return recent_messages
            else:
                logger.warning(
                    f"Session {session_id} not found in active sessions",
                    extra={"session_id": session_id},
                )
                return []

        except Exception as e:
            logger.error(
                f"Error retrieving conversation messages for session {session_id}: {e}",
                extra={
                    "session_id": session_id,
                    "error_type": type(e).__name__,
                    "window_size": self.max_recent_messages,
                },
            )
            return []

    async def add_message_to_memory(
        self,
        session_id: str,
        role: str,  # 'USER', 'ASSISTANT', 'SYSTEM'
        content: str,
        message_type: str = "TEXT",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add a message to conversation memory with comprehensive logging."""
        logger.debug(
            f"Adding {role} message to session {session_id}",
            extra={
                "session_id": session_id,
                "role": role,
                "message_type": message_type,
                "content_length": len(content),
                "has_metadata": bool(metadata),
            },
        )

        try:
            # Store message in active session
            if session_id in self.active_sessions:
                # Create LangChain message based on role
                if role.upper() == "USER":
                    message = HumanMessage(content=content)
                elif role.upper() == "ASSISTANT":
                    message = AIMessage(content=content)
                else:  # SYSTEM
                    message = SystemMessage(content=content)

                # Add message to session storage
                self.active_sessions[session_id]["messages"].append(message)

                # Apply sliding window: keep only recent messages
                messages = self.active_sessions[session_id]["messages"]
                if len(messages) > self.max_recent_messages:
                    self.active_sessions[session_id]["messages"] = messages[
                        -self.max_recent_messages :
                    ]

                logger.info(
                    f"Message added to session {session_id}",
                    extra={
                        "session_id": session_id,
                        "role": role.upper(),
                        "content_length": len(content),
                        "total_messages": len(
                            self.active_sessions[session_id]["messages"]
                        ),
                        "memory_strategy": "sliding_window",
                        "persistence": "in_memory",
                    },
                )

                return True
            else:
                logger.warning(
                    f"Session {session_id} not found, cannot add message",
                    extra={"session_id": session_id, "role": role},
                )
                return False

        except Exception as e:
            logger.error(
                f"Error adding message to session {session_id}: {e}",
                extra={
                    "session_id": session_id,
                    "role": role,
                    "error_type": type(e).__name__,
                },
            )
            return False

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters)."""
        return len(text) // 4

    async def _check_and_log_memory_status(self, session_id: str) -> None:
        """Check memory status and log for monitoring."""
        try:
            # TODO: Implement actual message counting when repository is available
            # For now, just log the check

            logger.debug(
                f"Memory status check for session {session_id}",
                extra={
                    "session_id": session_id,
                    "sliding_window_size": self.max_recent_messages,
                    "memory_strategy": "database_sliding_window",
                    "action": "memory_status_check",
                },
            )

        except Exception as e:
            logger.error(
                f"Error checking memory status for session {session_id}: {e}",
                extra={"session_id": session_id, "error_type": type(e).__name__},
            )

    def _convert_to_langchain_message(self, msg_data: Dict[str, Any]) -> BaseMessage:
        """Convert database message to LangChain message."""
        role = msg_data["role"]
        content = msg_data["content"]

        if role == "USER":
            return HumanMessage(content=content)
        elif role == "ASSISTANT":
            return AIMessage(content=content)
        else:  # SYSTEM
            return SystemMessage(content=content)

    async def get_active_sessions(self) -> Dict[str, Any]:
        """Get list of currently active sessions for debug purposes."""
        try:
            return {
                "total_active_sessions": len(self.active_sessions),
                "session_ids": list(self.active_sessions.keys()),
                "session_details": {
                    session_id: {
                        "topic": session_data.get("topic", "unknown"),
                        "difficulty": session_data.get("difficulty", "unknown"),
                        "start_time": (
                            session_data.get("start_time").isoformat()
                            if session_data.get("start_time")
                            else "unknown"
                        ),
                    }
                    for session_id, session_data in self.active_sessions.items()
                },
            }
        except Exception as e:
            logger.error(
                f"Error getting active sessions: {e}",
                extra={"error_type": type(e).__name__},
            )
            return {
                "total_active_sessions": 0,
                "session_ids": [],
                "session_details": {},
            }
