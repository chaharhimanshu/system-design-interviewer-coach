"""
Conversation Memory Management
Handles conversation context, history, and memory for AI agents
"""

import json
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict

from app.domain.entities.session import DifficultyLevel
from app.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class InteractionMemory:
    """Single interaction in conversation memory"""

    timestamp: datetime
    question: Optional[str] = None
    answer: Optional[str] = None
    evaluation: Optional[Dict[str, Any]] = None
    feedback: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    question_type: str = (
        "general"  # opening, follow_up, clarification, topic_transition
    )
    topics_covered: List[str] = None

    def __post_init__(self):
        if self.topics_covered is None:
            self.topics_covered = []


@dataclass
class SessionMemory:
    """Memory for an entire interview session"""

    session_id: UUID
    topic: str
    difficulty: DifficultyLevel
    start_time: datetime
    interactions: List[InteractionMemory]
    current_question: Optional[str] = None
    covered_topics: List[str] = None
    performance_trends: List[Dict[str, Any]] = None
    context_summary: Dict[str, Any] = None

    def __post_init__(self):
        if self.covered_topics is None:
            self.covered_topics = []
        if self.performance_trends is None:
            self.performance_trends = []
        if self.context_summary is None:
            self.context_summary = {}


class ConversationMemory:
    """
    Advanced conversation memory system for AI agents

    Capabilities:
    - Store and retrieve conversation history
    - Maintain context across interactions
    - Track performance trends over time
    - Provide contextual summaries
    - Manage memory efficiently with sliding windows
    """

    def __init__(
        self, max_memory_hours: int = 24, max_interactions_per_session: int = 100
    ):
        self.sessions: Dict[UUID, SessionMemory] = {}
        self.max_memory_hours = max_memory_hours
        self.max_interactions_per_session = max_interactions_per_session

        # Performance tracking
        self.performance_cache: Dict[UUID, List[Dict[str, Any]]] = defaultdict(list)

        logger.info("ConversationMemory initialized")

    async def initialize_session(
        self, session_id: UUID, topic: str, difficulty: DifficultyLevel
    ) -> None:
        """Initialize memory for a new session"""
        logger.info(f"Initializing memory for session {session_id}")

        self.sessions[session_id] = SessionMemory(
            session_id=session_id,
            topic=topic,
            difficulty=difficulty,
            start_time=datetime.utcnow(),
            interactions=[],
        )

    async def add_interaction(
        self,
        session_id: UUID,
        question: Optional[str] = None,
        answer: Optional[str] = None,
        evaluation: Optional[Dict[str, Any]] = None,
        feedback: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        question_type: str = "general",
        expected_topics: Optional[List[str]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Add a new interaction to session memory"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found in memory")

        session_memory = self.sessions[session_id]

        # Create interaction memory
        interaction = InteractionMemory(
            timestamp=timestamp or datetime.utcnow(),
            question=question,
            answer=answer,
            evaluation=evaluation,
            feedback=feedback,
            context=context,
            question_type=question_type,
            topics_covered=expected_topics or [],
        )

        # Add to session
        session_memory.interactions.append(interaction)

        # Update current question if provided
        if question:
            session_memory.current_question = question

        # Update covered topics
        if expected_topics:
            for topic in expected_topics:
                if topic not in session_memory.covered_topics:
                    session_memory.covered_topics.append(topic)

        # Update performance trends if evaluation provided
        if evaluation:
            self.performance_cache[session_id].append(
                {
                    "timestamp": interaction.timestamp,
                    "evaluation": evaluation,
                    "question_type": question_type,
                }
            )

        # Manage memory size
        await self._manage_memory_size(session_id)

        logger.debug(
            f"Added interaction to session {session_id}, total: {len(session_memory.interactions)}"
        )

    async def get_session_context(self, session_id: UUID) -> Dict[str, Any]:
        """Get comprehensive context for a session"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found in memory")

        session_memory = self.sessions[session_id]

        # Build context
        context = {
            "session_id": str(session_id),
            "topic": session_memory.topic,
            "difficulty": session_memory.difficulty.value,
            "start_time": session_memory.start_time.isoformat(),
            "current_question": session_memory.current_question,
            "covered_topics": session_memory.covered_topics,
            "interaction_count": len(session_memory.interactions),
            "recent_interactions": await self._get_recent_interactions(
                session_id, limit=5
            ),
            "performance_summary": await self._get_performance_summary(session_id),
            "conversation_flow": await self._analyze_conversation_flow(session_id),
        }

        return context

    async def get_conversation_history(
        self,
        session_id: UUID,
        limit: Optional[int] = None,
        include_evaluations: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        if session_id not in self.sessions:
            return []

        session_memory = self.sessions[session_id]
        interactions = session_memory.interactions

        if limit:
            interactions = interactions[-limit:]

        history = []
        for interaction in interactions:
            entry = {
                "timestamp": interaction.timestamp.isoformat(),
                "question": interaction.question,
                "answer": interaction.answer,
                "feedback": interaction.feedback,
                "question_type": interaction.question_type,
                "topics_covered": interaction.topics_covered,
            }

            if include_evaluations and interaction.evaluation:
                entry["evaluation"] = interaction.evaluation

            history.append(entry)

        return history

    async def get_performance_trends(
        self, session_id: UUID, window_size: int = 10
    ) -> List[Dict[str, Any]]:
        """Get performance trends for a session"""
        if session_id not in self.performance_cache:
            return []

        performance_data = self.performance_cache[session_id]

        # Return recent performance data
        return performance_data[-window_size:] if performance_data else []

    async def search_similar_interactions(
        self,
        session_id: UUID,
        query_topic: str,
        interaction_type: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search for similar interactions in the session"""
        if session_id not in self.sessions:
            return []

        session_memory = self.sessions[session_id]
        similar_interactions = []

        for interaction in session_memory.interactions:
            # Simple similarity check based on topics and type
            if interaction.topics_covered:
                topic_overlap = any(
                    query_topic.lower() in topic.lower()
                    for topic in interaction.topics_covered
                )
                if topic_overlap:
                    if (
                        not interaction_type
                        or interaction.question_type == interaction_type
                    ):
                        similar_interactions.append(
                            {
                                "timestamp": interaction.timestamp.isoformat(),
                                "question": interaction.question,
                                "answer": interaction.answer,
                                "question_type": interaction.question_type,
                                "topics_covered": interaction.topics_covered,
                            }
                        )

        return similar_interactions[-limit:]

    async def get_topic_coverage(self, session_id: UUID) -> Dict[str, Any]:
        """Get analysis of topic coverage for the session"""
        if session_id not in self.sessions:
            return {}

        session_memory = self.sessions[session_id]

        # Analyze topic coverage
        all_topics = []
        topic_frequency = defaultdict(int)

        for interaction in session_memory.interactions:
            if interaction.topics_covered:
                all_topics.extend(interaction.topics_covered)
                for topic in interaction.topics_covered:
                    topic_frequency[topic] += 1

        return {
            "total_topics_mentioned": len(set(all_topics)),
            "covered_topics": list(session_memory.covered_topics),
            "topic_frequency": dict(topic_frequency),
            "most_discussed": (
                max(topic_frequency.items(), key=lambda x: x[1])[0]
                if topic_frequency
                else None
            ),
            "coverage_depth": len(all_topics)
            / max(1, len(session_memory.interactions)),
        }

    async def cleanup_session(self, session_id: UUID) -> None:
        """Clean up memory for a completed session"""
        if session_id in self.sessions:
            del self.sessions[session_id]

        if session_id in self.performance_cache:
            del self.performance_cache[session_id]

        logger.info(f"Cleaned up memory for session {session_id}")

    async def cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions based on time threshold"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.max_memory_hours)
        expired_sessions = []

        for session_id, session_memory in self.sessions.items():
            if session_memory.start_time < cutoff_time:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            await self.cleanup_session(session_id)

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

    async def _get_recent_interactions(
        self, session_id: UUID, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get recent interactions for context"""
        session_memory = self.sessions[session_id]
        recent = (
            session_memory.interactions[-limit:] if session_memory.interactions else []
        )

        return [
            {
                "question": interaction.question,
                "answer": interaction.answer,
                "question_type": interaction.question_type,
                "timestamp": interaction.timestamp.isoformat(),
            }
            for interaction in recent
        ]

    async def _get_performance_summary(self, session_id: UUID) -> Dict[str, Any]:
        """Get performance summary for the session"""
        if session_id not in self.performance_cache:
            return {}

        performance_data = self.performance_cache[session_id]
        if not performance_data:
            return {}

        # Calculate averages
        total_scores = defaultdict(list)
        for data in performance_data:
            evaluation = data.get("evaluation", {})
            for key, value in evaluation.items():
                if key.endswith("_score") and isinstance(value, (int, float)):
                    total_scores[key].append(value)

        averages = {
            key: sum(scores) / len(scores) for key, scores in total_scores.items()
        }

        return {
            "total_evaluations": len(performance_data),
            "average_scores": averages,
            "recent_trend": "improving" if len(performance_data) > 1 else "initial",
        }

    async def _analyze_conversation_flow(self, session_id: UUID) -> Dict[str, Any]:
        """Analyze the flow of conversation"""
        session_memory = self.sessions[session_id]
        interactions = session_memory.interactions

        if not interactions:
            return {"flow_quality": "no_data"}

        # Analyze question types progression
        question_types = [i.question_type for i in interactions if i.question_type]

        # Count different types
        type_counts = defaultdict(int)
        for qtype in question_types:
            type_counts[qtype] += 1

        return {
            "total_interactions": len(interactions),
            "question_types_used": dict(type_counts),
            "flow_diversity": len(set(question_types)),
            "progression": (
                question_types[-5:] if len(question_types) >= 5 else question_types
            ),
        }

    async def _manage_memory_size(self, session_id: UUID) -> None:
        """Manage memory size to prevent excessive growth"""
        session_memory = self.sessions[session_id]

        if len(session_memory.interactions) > self.max_interactions_per_session:
            # Keep recent interactions and summarize older ones
            keep_count = self.max_interactions_per_session // 2

            # Store summary of older interactions
            older_interactions = session_memory.interactions[:-keep_count]
            session_memory.context_summary = await self._summarize_interactions(
                older_interactions
            )

            # Keep only recent interactions
            session_memory.interactions = session_memory.interactions[-keep_count:]

            logger.info(
                f"Managed memory size for session {session_id}, kept {keep_count} recent interactions"
            )

    async def _summarize_interactions(
        self, interactions: List[InteractionMemory]
    ) -> Dict[str, Any]:
        """Create a summary of older interactions"""
        if not interactions:
            return {}

        # Extract key information
        topics_discussed = []
        question_types = []
        evaluations = []

        for interaction in interactions:
            if interaction.topics_covered:
                topics_discussed.extend(interaction.topics_covered)
            if interaction.question_type:
                question_types.append(interaction.question_type)
            if interaction.evaluation:
                evaluations.append(interaction.evaluation)

        return {
            "summarized_interactions": len(interactions),
            "time_period": {
                "start": interactions[0].timestamp.isoformat(),
                "end": interactions[-1].timestamp.isoformat(),
            },
            "topics_discussed": list(set(topics_discussed)),
            "question_types": list(set(question_types)),
            "evaluation_count": len(evaluations),
        }
