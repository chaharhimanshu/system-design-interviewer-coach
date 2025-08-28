"""
AI Service
Main service that orchestrates AI agents for system design interviews
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
import asyncio

from app.domain.entities.session import InterviewSession, SessionStatus, DifficultyLevel
from app.shared.logging import get_logger
from app.shared.exceptions import ValidationError, ResourceNotFoundError

# Import AI agents
from app.agents.orchestrator.main_orchestrator import MainOrchestrator

logger = get_logger(__name__)


class AIService:
    """
    Main AI service that provides intelligent conversation capabilities
    for system design interviews

    Capabilities:
    - Start and manage interview sessions with AI
    - Process user responses and generate AI replies
    - Provide contextual feedback and guidance
    - Adapt difficulty dynamically based on performance
    - Manage conversation flow and memory
    """

    def __init__(self):
        self.orchestrator = MainOrchestrator()
        logger.info("AIService initialized with MainOrchestrator")

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

    async def process_user_response(
        self, session_id: UUID, user_message: str, message_type: str = "answer"
    ) -> Dict[str, Any]:
        """
        Process user's response and generate AI reply

        Args:
            session_id: The session identifier
            user_message: User's message/response
            message_type: Type of message (answer, question, clarification)

        Returns:
            Dict containing AI response, feedback, and guidance
        """
        logger.info(f"Processing user response for session {session_id}")

        try:
            # Process answer with orchestrator
            response = await self.orchestrator.process_user_answer(
                session_id=session_id,
                user_answer=user_message,
                message_type=message_type,
            )

            logger.info(
                f"Generated AI response for session {session_id}, type: {response.get('type', 'unknown')}"
            )
            return response

        except ValueError as e:
            logger.error(f"Session validation error: {str(e)}")
            raise ResourceNotFoundError(f"Session {session_id} not found or invalid")
        except Exception as e:
            logger.error(f"Failed to process user response: {str(e)}")
            raise

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
            session_state = await self.orchestrator.get_session_state(session_id)

            if not session_state:
                raise ResourceNotFoundError(f"Session {session_id} not found")

            # Extract insights from session state
            insights = {
                "session_id": str(session_id),
                "current_stage": session_state.get("stage", "unknown"),
                "performance_metrics": session_state.get("performance_metrics", {}),
                "covered_topics": session_state.get("covered_topics", []),
                "current_difficulty": session_state.get(
                    "difficulty_level", "intermediate"
                ),
                "follow_up_areas": session_state.get("follow_up_areas", []),
                "recommendations": await self._generate_session_recommendations(
                    session_state
                ),
            }

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
        Request a hint for the current question

        Args:
            session_id: The session identifier
            current_question: Current question user needs help with
            user_context: Optional context about where user is stuck

        Returns:
            Dict containing hint and guidance
        """
        logger.info(f"Generating hint for session {session_id}")

        try:
            session_state = await self.orchestrator.get_session_state(session_id)

            if not session_state:
                raise ResourceNotFoundError(f"Session {session_id} not found")

            # Generate hint using question generator
            hint_response = await self.orchestrator.question_generator.generate_clarification_question(
                topic=session_state["topic"],
                difficulty=session_state["difficulty_level"],
                evaluation={
                    "needs_clarification": True,
                    "areas_needing_help": [user_context or "general guidance"],
                    "current_question": current_question,
                },
            )

            return {
                "type": "hint",
                "hint": hint_response["question"],
                "guidance": hint_response.get("guidance", ""),
                "context": hint_response.get("context", ""),
                "session_id": str(session_id),
            }

        except Exception as e:
            logger.error(f"Failed to generate hint: {str(e)}")
            raise

    async def get_interview_feedback(self, session_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive interview feedback

        Args:
            session_id: The session identifier

        Returns:
            Dict containing detailed feedback and recommendations
        """
        logger.info(f"Generating comprehensive feedback for session {session_id}")

        try:
            session_state = await self.orchestrator.get_session_state(session_id)

            if not session_state:
                raise ResourceNotFoundError(f"Session {session_id} not found")

            # Get conversation context
            context = await self.orchestrator.memory.get_session_context(session_id)

            # Generate final feedback
            final_feedback = (
                await self.orchestrator.feedback_provider.generate_final_feedback(
                    performance_metrics=session_state["performance_metrics"],
                    topic=session_state["topic"],
                    difficulty=session_state["difficulty_level"],
                    context=context,
                )
            )

            return final_feedback

        except Exception as e:
            logger.error(f"Failed to generate interview feedback: {str(e)}")
            raise

    async def suggest_follow_up_topics(
        self, session_id: UUID, completed_topics: List[str]
    ) -> Dict[str, Any]:
        """
        Suggest follow-up topics based on session progress

        Args:
            session_id: The session identifier
            completed_topics: Topics already covered

        Returns:
            Dict containing suggested topics and rationale
        """
        logger.info(f"Suggesting follow-up topics for session {session_id}")

        try:
            session_state = await self.orchestrator.get_session_state(session_id)

            if not session_state:
                raise ResourceNotFoundError(f"Session {session_id} not found")

            # Get context for suggestions
            context = await self.orchestrator.memory.get_session_context(session_id)

            # Generate next topic suggestions
            suggestions = (
                await self.orchestrator.question_generator.generate_next_topic_question(
                    main_topic=session_state["topic"],
                    difficulty=session_state["difficulty_level"],
                    covered_topics=completed_topics,
                    context=context,
                )
            )

            return suggestions

        except Exception as e:
            logger.error(f"Failed to suggest follow-up topics: {str(e)}")
            raise

    async def adapt_difficulty(
        self, session_id: UUID, performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Dynamically adapt interview difficulty based on performance

        Args:
            session_id: The session identifier
            performance_data: Recent performance data

        Returns:
            Dict containing difficulty adjustment recommendation
        """
        logger.info(f"Evaluating difficulty adaptation for session {session_id}")

        try:
            session_state = await self.orchestrator.get_session_state(session_id)

            if not session_state:
                raise ResourceNotFoundError(f"Session {session_id} not found")

            # Check if difficulty should be adjusted
            should_adjust, new_difficulty = (
                await self.orchestrator.difficulty_adaptor.should_adjust_difficulty(
                    current_difficulty=session_state["difficulty_level"],
                    performance_metrics=session_state["performance_metrics"],
                    evaluation=performance_data,
                )
            )

            if should_adjust and new_difficulty:
                # Update session difficulty
                session_state["difficulty_level"] = new_difficulty

                logger.info(
                    f"Difficulty adjusted for session {session_id}: {new_difficulty}"
                )

                return {
                    "adjusted": True,
                    "new_difficulty": new_difficulty.value,
                    "session_id": str(session_id),
                }
            else:
                return {
                    "adjusted": False,
                    "current_difficulty": session_state["difficulty_level"].value,
                    "session_id": str(session_id),
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
        Get a summary of the conversation so far

        Args:
            session_id: The session identifier

        Returns:
            Dict containing conversation summary
        """
        logger.info(f"Getting conversation summary for session {session_id}")

        try:
            # Get conversation history from memory
            history = await self.orchestrator.memory.get_conversation_history(
                session_id=session_id, limit=None, include_evaluations=True
            )

            # Get topic coverage
            topic_coverage = await self.orchestrator.memory.get_topic_coverage(
                session_id
            )

            # Get performance trends
            performance_trends = await self.orchestrator.memory.get_performance_trends(
                session_id=session_id, window_size=10
            )

            return {
                "session_id": str(session_id),
                "total_interactions": len(history),
                "topic_coverage": topic_coverage,
                "performance_trends": performance_trends,
                "conversation_highlights": self._extract_conversation_highlights(
                    history
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get conversation summary: {str(e)}")
            raise

    async def _generate_session_recommendations(
        self, session_state: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on session state"""
        recommendations = []

        metrics = session_state.get("performance_metrics", {})

        # Performance-based recommendations
        if metrics.get("clarity_score", 0) < 6:
            recommendations.append(
                "Focus on structuring your explanations more clearly"
            )

        if metrics.get("technical_depth", 0) < 6:
            recommendations.append(
                "Provide more specific technical details in your answers"
            )

        if metrics.get("scalability_awareness", 0) < 6:
            recommendations.append("Consider scalability implications more thoroughly")

        if metrics.get("trade_offs_understanding", 0) < 6:
            recommendations.append("Discuss trade-offs between different approaches")

        # Stage-based recommendations
        stage = session_state.get("stage", "ongoing")
        if stage == "opening":
            recommendations.append(
                "Take time to understand requirements before diving into solutions"
            )

        return recommendations

    def _extract_conversation_highlights(
        self, history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract key highlights from conversation history"""
        highlights = []

        for interaction in history[-5:]:  # Last 5 interactions
            if interaction.get("evaluation"):
                eval_data = interaction["evaluation"]
                if any(
                    score >= 8
                    for score in eval_data.values()
                    if isinstance(score, (int, float))
                ):
                    highlights.append(
                        {
                            "type": "strength",
                            "timestamp": interaction["timestamp"],
                            "description": "Strong performance on this topic",
                        }
                    )

        return highlights
