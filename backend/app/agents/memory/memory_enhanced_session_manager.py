"""
Memory-Enhanced Session Manager
Manages cross-agent memory using LangGraph MemorySaver checkpointer
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
import logging

from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.agents.models.output_schemas import MemoryEnhancedInterviewState
from app.shared.logging import get_logger

logger = get_logger(__name__)


class MemoryEnhancedSessionManager:
    """
    Session manager that provides cross-agent memory using LangGraph MemorySaver.

    Key Features:
    - Automatic context sharing between agents
    - Persistent conversation history
    - Thread-based session management
    - State persistence across tool calls
    """

    def __init__(self):
        # Add instance tracking for debugging
        self.instance_id = datetime.utcnow().isoformat()

        # Initialize LangGraph memory
        self.memory_saver = MemorySaver()

        # Track active sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        logger.info(
            f"MemoryEnhancedSessionManager initialized with LangGraph MemorySaver, instance: {self.instance_id}"
        )

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

    async def initialize_session(
        self,
        session_id: str,
        topic: str,
        difficulty: str,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> MemoryEnhancedInterviewState:
        """
        Initialize a new session with enhanced state.

        Args:
            session_id: Unique session identifier
            topic: Interview topic
            difficulty: Difficulty level
            user_context: Additional user context

        Returns:
            Initial enhanced state
        """
        logger.info(f"Initializing memory-enhanced session: {session_id}")

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

        # Store session metadata
        self.active_sessions[session_id] = {
            "topic": topic,
            "difficulty": difficulty,
            "start_time": datetime.utcnow(),
            "user_context": user_context or {},
            "state": initial_state,
        }

        # Add initial system message to memory
        config = self.get_config(session_id)
        initial_messages = [
            SystemMessage(
                content=f"""Interview Session Started
Topic: {topic}
Difficulty: {difficulty}
Context: This is the beginning of a system design interview session."""
            )
        ]

        # Initialize memory with system message
        logger.info(f"Session {session_id} initialized with memory")
        return initial_state

    async def add_answer_to_memory(
        self,
        session_id: str,
        answer: str,
        answer_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Store user answer in session state for agents to access.
        Memory persistence is handled automatically by LangGraph agents.

        Args:
            session_id: Session identifier
            answer: User's answer
            answer_context: Additional context about the answer
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found for answer logging")
            return

        # Store answer in session state for agent access
        session_data = self.active_sessions[session_id]
        if "state" in session_data:
            session_data["state"].last_user_answer = answer
            session_data["state"].last_answer_context = answer_context or {}

        logger.info(
            f"User answer stored in session state for {session_id}",
            extra={
                "session_id": session_id,
                "answer_preview": answer[:100] + "..." if len(answer) > 100 else answer,
                "answer_length": len(answer),
                "context_keys": list(answer_context.keys()) if answer_context else [],
            },
        )

    async def add_evaluation_to_memory(
        self, session_id: str, evaluation: Dict[str, Any]
    ):
        """
        Add evaluation results to shared memory.

        Args:
            session_id: Session identifier
            evaluation: Evaluation results
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found for evaluation logging")
            return

        # Update session state
        session_data = self.active_sessions[session_id]
        if "state" in session_data:
            session_data["state"].evaluation_history.append(evaluation)

        # Create system message for evaluation
        system_message = SystemMessage(
            content="Answer evaluation completed",
            additional_kwargs={
                "type": "evaluation",
                "evaluation": evaluation,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        logger.debug(f"Evaluation added to memory for session {session_id}")

    async def update_session_state(
        self, session_id: str, state_updates: Dict[str, Any]
    ):
        """
        Update session state information.

        Args:
            session_id: Session identifier
            state_updates: State updates to apply
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found for state update")
            return

        session_data = self.active_sessions[session_id]
        if "state" in session_data:
            # Update state fields
            for key, value in state_updates.items():
                if hasattr(session_data["state"], key):
                    setattr(session_data["state"], key, value)
                    logger.debug(f"Updated {key} in session {session_id}")

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

    def get_memory_saver(self) -> MemorySaver:
        """Get the LangGraph MemorySaver instance for agent creation."""
        return self.memory_saver

    async def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        return list(self.active_sessions.keys())

    async def get_session_metrics(self) -> Dict[str, Any]:
        """Get overall session metrics."""
        return {
            "total_active_sessions": len(self.active_sessions),
            "memory_saver_type": type(self.memory_saver).__name__,
            "sessions": list(self.active_sessions.keys()),
        }

    async def get_memory_contents(self, session_id: str) -> Dict[str, Any]:
        """
        Get the actual memory contents from LangGraph for debugging.

        Args:
            session_id: Session identifier

        Returns:
            Memory contents including all messages and checkpoints
        """
        try:
            config = self.get_config(session_id)

            # Get the latest checkpoint from memory
            checkpoint = await self.memory_saver.aget(config)

            if not checkpoint:
                return {
                    "session_id": session_id,
                    "memory_status": "no_checkpoint_found",
                    "messages": [],
                    "checkpoint_data": None,
                }

            # Extract messages from checkpoint
            messages = []
            if (
                hasattr(checkpoint, "channel_values")
                and "messages" in checkpoint.channel_values
            ):
                messages = checkpoint.channel_values["messages"]

            return {
                "session_id": session_id,
                "memory_status": "found",
                "total_messages": len(messages) if messages else 0,
                "messages": (
                    [
                        {
                            "type": type(msg).__name__,
                            "content": (
                                msg.content[:200] + "..."
                                if len(str(msg.content)) > 200
                                else str(msg.content)
                            ),
                            "timestamp": getattr(msg, "additional_kwargs", {}).get(
                                "timestamp", "unknown"
                            ),
                        }
                        for msg in messages
                    ]
                    if messages
                    else []
                ),
                "checkpoint_id": getattr(checkpoint, "id", "unknown"),
                "checkpoint_timestamp": getattr(checkpoint, "ts", "unknown"),
                "config_used": config,
            }

        except Exception as e:
            logger.error(f"Error getting memory contents for session {session_id}: {e}")
            return {
                "session_id": session_id,
                "memory_status": "error",
                "error": str(e),
                "config_used": self.get_config(session_id),
            }

    async def list_all_memory_threads(self) -> Dict[str, Any]:
        """
        List all memory threads stored in the checkpointer.
        Useful for debugging what's actually stored in memory.
        """
        try:
            # Get all stored thread IDs (this might not be directly available in MemorySaver)
            active_threads = []
            memory_summary = {}

            for session_id in self.active_sessions.keys():
                memory_contents = await self.get_memory_contents(session_id)
                active_threads.append(
                    {
                        "session_id": session_id,
                        "memory_status": memory_contents["memory_status"],
                        "message_count": memory_contents.get("total_messages", 0),
                    }
                )

            return {
                "total_threads": len(active_threads),
                "active_threads": active_threads,
                "memory_saver_type": type(self.memory_saver).__name__,
            }

        except Exception as e:
            logger.error(f"Error listing memory threads: {e}")
            return {
                "error": str(e),
                "memory_saver_type": type(self.memory_saver).__name__,
            }
