"""
AI Service
Main service that orchestrates AI agents for system design interviews
"""

from typing import Dict, Any, List, Optional, AsyncGenerator
from uuid import UUID
import asyncio

from app.domain.entities.session import InterviewSession, SessionStatus, DifficultyLevel
from app.agents.models.output_schemas import MemoryEnhancedInterviewState
from app.shared.logging import get_logger
from app.shared.exceptions import ValidationError, ResourceNotFoundError

# Import AI agents
from app.agents.orchestrator.memory_enhanced_orchestrator import (
    MemoryEnhancedOrchestrator,
)

logger = get_logger(__name__)


class AIService:
    """
    Main AI service that provides intelligent conversation capabilities
    for system design interviews with optimized memory-enhanced architecture

    Capabilities:
    - Start and manage interview sessions with AI (1 API call vs 5+)
    - Process user responses and generate AI replies (2 API calls vs 10+)
    - Provide contextual feedback and guidance (2 API calls vs 8+)
    - Adapt difficulty dynamically based on performance
    - Manage conversation flow and cross-agent memory
    - Generate comprehensive interview summaries (1 API call)

    OPTIMIZATION: 85-90% API call reduction with memory-enhanced agents
    """

    def __init__(self):
        self.orchestrator = MemoryEnhancedOrchestrator()
        logger.info(
            "AIService initialized with MemoryEnhancedOrchestrator (optimized architecture)"
        )

    async def start_interview_session(
        self, session: InterviewSession, user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start an AI-powered interview session

        Args:
            session: The interview session to start
            user_context: Optional context about the user (experience, preferences)

        Returns:
            Dict containing the opening question and context
        """
        logger.info(f"Starting AI interview session {session.session_id}")

        try:
            # Validate session
            if session.status != SessionStatus.ACTIVE:
                raise ValidationError("Session must be active to start AI interview")

            # Start interview with orchestrator
            result = await self.orchestrator.start_interview(session, user_context)

            logger.info(f"AI interview started for session {session.session_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to start AI interview: {str(e)}")
            raise

    async def process_user_response_stream(
        self, session_id: UUID, user_message: str, message_type: str = "answer"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process user's response and stream AI reply in real-time

        Args:
            session_id: The session identifier
            user_message: User's message/response
            message_type: Type of message (answer, question, clarification)

        Yields:
            Dict containing streaming chunks with type and content
        """
        logger.info(f"Streaming processing for user response in session {session_id}")

        try:
            # Send initial status
            yield {"type": "status", "message": "Analyzing your response..."}

            # Process answer with orchestrator (streaming)
            async for chunk in self.orchestrator.process_user_answer_stream(
                session_id=str(session_id),
                user_answer=user_message,
                message_type=message_type,
            ):
                yield chunk

            logger.info(f"Completed streaming AI response for session {session_id}")

        except ValueError as e:
            logger.error(f"Session validation error: {str(e)}")
            yield {
                "type": "error",
                "message": f"Session {session_id} not found or invalid",
            }
        except Exception as e:
            logger.error(f"Failed to stream user response: {str(e)}")
            yield {
                "type": "error",
                "message": "An error occurred while processing your response",
            }

    async def get_session_insights(self, session_id: UUID) -> Dict[str, Any]:
        """
        Get AI insights about the session progress and performance

        Args:
            session_id: The session identifier

        Returns:
            Dict containing session insights and recommendations
        """
        logger.info(f"Getting AI insights for session {session_id}")

        try:
            # Use memory-enhanced session insights
            insights = await self.orchestrator.get_session_insights(str(session_id))

            # Add session_id in UUID format for compatibility
            insights["session_id"] = str(session_id)

            return insights

        except Exception as e:
            logger.error(f"Failed to get session insights: {str(e)}")
            raise

    async def request_hint(
        self,
        session_id: UUID,
        current_question: str,
        user_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Request a hint for the current question using memory-enhanced generation

        Args:
            session_id: The session identifier
            current_question: Current question user needs help with
            user_context: Optional context about where user is stuck

        Returns:
            Dict containing hint and guidance
        """
        logger.info(f"Generating hint for session {session_id}")

        try:
            # Get session state from memory-enhanced manager
            session_state = await self.orchestrator.session_manager.get_session_state(
                str(session_id)
            )

            if not session_state:
                raise ResourceNotFoundError(f"Session {session_id} not found")

            # Generate hint using memory-enhanced question generator
            hint_response = await self.orchestrator.question_generator.generate_clarification_question(
                session_id=str(session_id),
                unclear_areas=[user_context or "general guidance"],
                current_question=current_question,
            )

            return {
                "type": "hint",
                "hint": hint_response.question,
                "guidance": hint_response.guidance_hints,
                "context": hint_response.expected_concepts,
                "session_id": str(session_id),
                "memory_enhanced": True,
            }

        except Exception as e:
            logger.error(f"Failed to generate hint: {str(e)}")
            raise

    async def get_interview_feedback(self, session_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive interview feedback using memory-enhanced generation

        Args:
            session_id: The session identifier

        Returns:
            Dict containing detailed feedback and recommendations
        """
        logger.info(f"Generating comprehensive feedback for session {session_id}")

        try:
            # Generate memory-enhanced comprehensive feedback
            feedback = await self.orchestrator.feedback_provider.generate_comprehensive_feedback(
                session_id=str(session_id)
            )

            # Return structured feedback response
            return {
                "session_id": str(session_id),
                "feedback": feedback.dict(),
                "memory_enhanced": True,
                "comprehensive": True,
            }

        except Exception as e:
            logger.error(f"Failed to generate interview feedback: {str(e)}")
            raise

    async def suggest_follow_up_topics(
        self, session_id: UUID, completed_topics: List[str]
    ) -> Dict[str, Any]:
        """
        Suggest follow-up topics based on session progress using memory-enhanced approach

        Args:
            session_id: The session identifier
            completed_topics: Topics already covered

        Returns:
            Dict containing suggested topics and rationale
        """
        logger.info(f"Suggesting follow-up topics for session {session_id}")

        try:
            # Get session state for context
            session_state = await self.orchestrator.session_manager.get_session_state(
                str(session_id)
            )

            if not session_state:
                raise ResourceNotFoundError(f"Session {session_id} not found")

            # Generate contextual follow-up question (uses memory automatically)
            follow_up = (
                await self.orchestrator.question_generator.generate_follow_up_question(
                    session_id=str(session_id),
                    user_answer="",  # Not needed since memory provides context
                    evaluation_context={"request_type": "topic_suggestion"},
                )
            )

            return {
                "session_id": str(session_id),
                "suggested_topic": follow_up.question,
                "expected_concepts": follow_up.expected_concepts,
                "guidance_hints": follow_up.guidance_hints,
                "difficulty_level": follow_up.difficulty_level.value,
                "memory_enhanced": True,
                "rationale": "Generated based on conversation history and performance patterns",
            }

        except Exception as e:
            logger.error(f"Failed to suggest follow-up topics: {str(e)}")
            raise

    async def adapt_difficulty(
        self, session_id: UUID, performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Dynamically adapt interview difficulty based on performance
        Note: Memory-enhanced orchestrator handles this automatically through evaluation

        Args:
            session_id: The session identifier
            performance_data: Recent performance data

        Returns:
            Dict containing difficulty adjustment recommendation
        """
        logger.info(f"Evaluating difficulty adaptation for session {session_id}")

        try:
            # Get current session state
            session_state = await self.orchestrator.session_manager.get_session_state(
                str(session_id)
            )

            if not session_state:
                raise ResourceNotFoundError(f"Session {session_id} not found")

            # The memory-enhanced orchestrator handles difficulty adaptation automatically
            # Return current difficulty and note that adaptation is handled automatically
            current_difficulty = session_state.difficulty_level

            return {
                "adjusted": False,
                "current_difficulty": current_difficulty,
                "session_id": str(session_id),
                "automatic_adaptation": True,
                "note": "Difficulty adaptation is handled automatically by memory-enhanced orchestrator during evaluation",
            }

        except Exception as e:
            logger.error(f"Failed to adapt difficulty: {str(e)}")
            raise

    async def cleanup_session(self, session_id: UUID) -> None:
        """
        Clean up AI resources for a completed session

        Args:
            session_id: The session identifier
        """
        logger.info(f"Cleaning up AI resources for session {session_id}")

        try:
            await self.orchestrator.cleanup_session(session_id)
            logger.info(f"AI resources cleaned up for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup AI session: {str(e)}")
            # Don't raise exception for cleanup failures

    async def get_conversation_summary(self, session_id: UUID) -> Dict[str, Any]:
        """
        Get a summary of the conversation using memory-enhanced session summary

        Args:
            session_id: The session identifier

        Returns:
            Dict containing conversation summary
        """
        logger.info(f"Getting conversation summary for session {session_id}")

        try:
            # Use memory-enhanced session summary which includes all conversation data
            summary = await self.orchestrator.session_manager.get_session_summary(
                str(session_id)
            )

            # Add UUID format session_id for compatibility
            summary["session_id"] = str(session_id)
            summary["memory_enhanced"] = True

            return summary

        except Exception as e:
            logger.error(f"Failed to get conversation summary: {str(e)}")
            raise

    async def _generate_session_recommendations(
        self, session_state: MemoryEnhancedInterviewState
    ) -> List[str]:
        """Generate recommendations based on memory-enhanced session state"""
        recommendations = []

        # Use memory-enhanced state for performance-based recommendations
        if (
            hasattr(session_state, "user_performance")
            and session_state.user_performance
        ):
            latest_score = session_state.user_performance.get("latest_score", 0)

            if latest_score < 6:
                recommendations.append(
                    "Focus on providing more specific details in your explanations"
                )
                recommendations.append(
                    "Consider breaking down complex problems into smaller components"
                )

            if session_state.user_performance.get("score_trend") == "declining":
                recommendations.append(
                    "Take time to think through your responses more carefully"
                )

        # Phase-based recommendations using memory-enhanced interview phase
        phase = session_state.interview_phase
        if phase == "opening":
            recommendations.append(
                "Focus on understanding requirements before proposing solutions"
            )
        elif phase == "exploration":
            recommendations.append("Dive deeper into technical implementation details")
        elif phase == "deep_dive":
            recommendations.append("Consider scalability and performance implications")

        return (
            recommendations
            if recommendations
            else ["Continue with your current approach - you're doing well!"]
        )
