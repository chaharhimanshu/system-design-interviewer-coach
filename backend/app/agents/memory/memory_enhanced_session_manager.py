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
            f"Initializing session with unified memory context",
            extra={
                "session_id": session_id,
                "topic": topic,
                "difficulty": difficulty,
                "has_user_context": bool(user_context),
                "memory_manager_instance": self.instance_id,
                "sliding_window_size": self.max_recent_messages,
            },
        )

        # Create initial state with new unified memory structure
        initial_state = MemoryEnhancedInterviewState(
            interview_session_id=session_id,
            current_topic=topic,
            difficulty_level=difficulty,
            interview_phase="opening",
            question_count=0,
            conversation_history=[],
            conversation_flow_state="ready_for_opening",
            evaluation_history=[],
            last_question=None,
            last_user_answer=None,
        )

        # Store session metadata
        session_metadata = {
            "topic": topic,
            "difficulty": difficulty,
            "start_time": datetime.utcnow(),
            "user_context": user_context or {},
            "state": initial_state,
        }

        self.active_sessions[session_id] = session_metadata

        # Add system message to conversation history
        await self.add_conversation_turn(
            session_id=session_id,
            role="AI",
            content=f"Interview session started - Topic: {topic}, Difficulty: {difficulty}",
            turn_type="system",
        )

        logger.info(
            f"Session initialized successfully with unified memory context",
            extra={
                "session_id": session_id,
                "topic": topic,
                "difficulty": difficulty,
                "initial_phase": initial_state.interview_phase,
                "conversation_flow_state": initial_state.conversation_flow_state,
                "active_sessions_count": len(self.active_sessions),
                "memory_strategy": "unified_conversation_context",
            },
        )

        return initial_state

    async def add_conversation_turn(
        self,
        session_id: str,
        role: str,  # 'AI' or 'User'
        content: str,
        turn_type: str = "message",  # 'question', 'answer', 'system', 'message'
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add a conversation turn to the unified conversation history.

        Args:
            session_id: Session identifier
            role: 'AI' or 'User'
            content: Content of the message
            turn_type: Type of turn ('question', 'answer', 'system', 'message')
            metadata: Additional metadata for the turn

        Returns:
            True if successful, False otherwise
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found for conversation turn")
            return False

        session_data = self.active_sessions[session_id]
        state = session_data.get("state")

        if not state:
            logger.error(f"No state found for session {session_id}")
            return False

        # Create conversation turn
        turn = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow(),
            "type": turn_type,
            "metadata": metadata or {},
        }

        # Add to conversation history
        state.conversation_history.append(turn)

        # Apply sliding window to conversation history
        if len(state.conversation_history) > self.max_recent_messages:
            state.conversation_history = state.conversation_history[
                -self.max_recent_messages :
            ]

        # Update quick reference fields
        if role == "AI" and turn_type == "question":
            state.last_question = content
        elif role == "User" and turn_type == "answer":
            state.last_user_answer = content

        logger.info(
            f"Conversation turn added to session {session_id}",
            extra={
                "session_id": session_id,
                "role": role,
                "turn_type": turn_type,
                "content_length": len(content),
                "total_turns": len(state.conversation_history),
                "memory_strategy": "unified_conversation_context",
            },
        )

        return True

    async def update_conversation_flow_state(
        self, session_id: str, new_state: str
    ) -> bool:
        """
        Update the conversation flow state.

        Args:
            session_id: Session identifier
            new_state: New flow state

        Returns:
            True if successful, False otherwise
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found for flow state update")
            return False

        session_data = self.active_sessions[session_id]
        state = session_data.get("state")

        if not state:
            logger.error(f"No state found for session {session_id}")
            return False

        old_state = state.conversation_flow_state
        state.conversation_flow_state = new_state

        logger.info(
            f"Conversation flow state updated for session {session_id}",
            extra={
                "session_id": session_id,
                "old_state": old_state,
                "new_state": new_state,
                "memory_action": "flow_state_updated",
            },
        )

        return True

    async def get_conversation_context_for_prompt(
        self, session_id: str, max_turns: Optional[int] = None
    ) -> str:
        """
        Get conversation context formatted for AI prompts.

        Args:
            session_id: Session identifier
            max_turns: Maximum number of recent turns to include

        Returns:
            Formatted conversation context string
        """
        if session_id not in self.active_sessions:
            return ""

        state = self.active_sessions[session_id].get("state")
        if not state or not state.conversation_history:
            return ""

        # Get recent turns
        turns_to_include = max_turns or self.max_recent_messages
        recent_turns = state.conversation_history[-turns_to_include:]

        # Format for prompt
        context_lines = []
        for turn in recent_turns:
            if turn["type"] == "system":
                context_lines.append(f"SYSTEM: {turn['content']}")
            elif turn["role"] == "AI":
                context_lines.append(f"AI: {turn['content']}")
            elif turn["role"] == "User":
                context_lines.append(f"User: {turn['content']}")

        return "\n".join(context_lines)

    async def get_performance_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get performance summary from evaluation history.

        Args:
            session_id: Session identifier

        Returns:
            Performance summary dictionary
        """
        if session_id not in self.active_sessions:
            return {}

        state = self.active_sessions[session_id].get("state")
        if not state or not state.evaluation_history:
            return {"average_score": 0, "evaluation_count": 0, "trend": "no_data"}

        evaluations = state.evaluation_history

        # Calculate average score
        scores = []
        for eval_data in evaluations:
            if "scores" in eval_data and "average_score" in eval_data["scores"]:
                scores.append(eval_data["scores"]["average_score"])

        avg_score = sum(scores) / len(scores) if scores else 0

        # Determine trend
        trend = "stable"
        if len(scores) >= 2:
            recent_avg = sum(scores[-2:]) / 2
            earlier_avg = (
                sum(scores[:-2]) / len(scores[:-2]) if len(scores) > 2 else scores[0]
            )
            if recent_avg > earlier_avg + 0.5:
                trend = "improving"
            elif recent_avg < earlier_avg - 0.5:
                trend = "declining"

        return {
            "average_score": avg_score,
            "evaluation_count": len(evaluations),
            "trend": trend,
            "latest_score": scores[-1] if scores else 0,
            "score_history": scores,
        }

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
        state = session_data.get("state")
        if state:
            state.evaluation_history.append(evaluation)
            evaluation_count = len(state.evaluation_history)
        else:
            evaluation_count = 0

        logger.info(
            f"Evaluation added to session memory",
            extra={
                "session_id": session_id,
                "evaluation_keys": list(evaluation.keys()) if evaluation else [],
                "total_evaluations": evaluation_count,
                "overall_score": evaluation.get("scores", {}).get(
                    "average_score", "N/A"
                ),
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
        state = session_data.get("state")
        updated_fields = []

        if state:
            # Track what gets updated
            for key, new_value in state_updates.items():
                if hasattr(state, key):
                    old_value = getattr(state, key, None)
                    setattr(state, key, new_value)
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
            "conversation_flow_state": state.conversation_flow_state,
            "interview_phase": state.interview_phase,
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
            and state.conversation_flow_state
            != "generating_followup"  # Use flow state instead
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
        Get the actual memory contents for debugging.

        Args:
            session_id: Session identifier

        Returns:
            Memory contents including all conversation turns and state
        """
        try:
            session_in_active = session_id in self.active_sessions
            state = (
                self.active_sessions.get(session_id, {}).get("state")
                if session_in_active
                else None
            )

            conversation_context = ""
            if state and state.conversation_history:
                conversation_context = await self.get_conversation_context_for_prompt(
                    session_id
                )

            return {
                "session_id": session_id,
                "memory_status": "active" if session_in_active else "not_found",
                "memory_type": "unified_conversation_context",
                "sliding_window_size": self.max_recent_messages,
                "total_conversation_turns": (
                    len(state.conversation_history) if state else 0
                ),
                "conversation_history": state.conversation_history if state else [],
                "conversation_context_formatted": conversation_context,
                "conversation_flow_state": (
                    state.conversation_flow_state if state else None
                ),
                "session_state": (
                    {
                        "interview_session_id": state.interview_session_id,
                        "current_topic": state.current_topic,
                        "difficulty_level": state.difficulty_level,
                        "interview_phase": state.interview_phase,
                        "question_count": state.question_count,
                        "evaluation_history_count": len(state.evaluation_history),
                        "last_question": state.last_question,
                        "last_user_answer": state.last_user_answer,
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
                "memory_connection": "failed",
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
        Get recent conversation messages as LangChain BaseMessage objects.

        Args:
            session_id: Session identifier

        Returns:
            List of recent LangChain messages (for compatibility)
        """
        logger.debug(
            f"Retrieving conversation messages for session {session_id} with sliding window size: {self.max_recent_messages}"
        )

        try:
            if session_id not in self.active_sessions:
                logger.warning(f"Session {session_id} not found in active sessions")
                return []

            state = self.active_sessions[session_id].get("state")
            if not state or not state.conversation_history:
                return []

            # Convert conversation history to LangChain messages
            messages = []
            for turn in state.conversation_history:
                if turn["role"] == "AI":
                    messages.append(AIMessage(content=turn["content"]))
                elif turn["role"] == "User":
                    messages.append(HumanMessage(content=turn["content"]))
                else:  # System
                    messages.append(SystemMessage(content=turn["content"]))

            logger.info(
                f"Conversation messages retrieved for session {session_id}",
                extra={
                    "session_id": session_id,
                    "messages_found": len(messages),
                    "total_turns": len(state.conversation_history),
                    "memory_strategy": "unified_conversation_context",
                },
            )

            return messages

        except Exception as e:
            logger.error(
                f"Error retrieving conversation messages for session {session_id}: {e}",
                extra={
                    "session_id": session_id,
                    "error_type": type(e).__name__,
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
        """
        Add a message to conversation memory (compatibility method).

        This method maintains compatibility with existing code while using the new
        unified conversation context internally.

        Args:
            session_id: Session identifier
            role: Message role ('USER', 'ASSISTANT', 'SYSTEM')
            content: Message content
            message_type: Type of message
            metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        # Map old role format to new format
        role_mapping = {"USER": "User", "ASSISTANT": "AI", "SYSTEM": "AI"}

        new_role = role_mapping.get(role.upper(), "AI")

        # Map message type
        turn_type = "message"
        if message_type == "QUESTION":
            turn_type = "question"
        elif message_type == "ANSWER":
            turn_type = "answer"
        elif message_type == "SYSTEM":
            turn_type = "system"

        return await self.add_conversation_turn(
            session_id=session_id,
            role=new_role,
            content=content,
            turn_type=turn_type,
            metadata=metadata,
        )

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
