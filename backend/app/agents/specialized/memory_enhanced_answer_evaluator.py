"""
Memory-Enhanced Answer Evaluator Agent
Single API call evaluator with conversation memory and JSON structured outputs
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from app.domain.entities.session import DifficultyLevel
from app.agents.models.output_schemas import (
    AnswerEvaluation,
    EvaluationScores,
    AnswerAnalysis,
    NextSteps,
)
from app.agents.memory.memory_enhanced_session_manager import (
    MemoryEnhancedSessionManager,
)
from app.infrastructure.config.settings import get_settings
from app.agents.prompts import (
    ANSWER_EVALUATOR_SYSTEM_PROMPT,
    ANSWER_EVALUATION_PROMPT_TEMPLATE,
)
from app.shared.logging import get_logger

logger = get_logger(__name__)


class MemoryEnhancedAnswerEvaluator:
    """
    Memory-Enhanced Answer Evaluator with database memory and agent pattern.

    Optimizations:
    - Uses LangGraph agent pattern with database memory (no checkpointer)
    - JSON-structured prompting for consistent outputs
    - Single API call (no tools) - 85% API reduction
    - Cross-agent memory sharing via database session manager
    - Rich interview context for intelligent evaluations
    """

    def __init__(self, session_manager: MemoryEnhancedSessionManager):
        self.settings = get_settings()
        self.session_manager = session_manager

        # Initialize OpenAI model with optimized settings
        self.llm = ChatOpenAI(
            model=self.settings.openai.model,
            temperature=0.2,  # Lower temperature for consistent evaluations
            api_key=self.settings.openai.api_key,
            max_tokens=self.settings.openai.max_tokens,
        )

        # Create React agent WITHOUT checkpointer - we handle memory via database
        self.agent = create_react_agent(
            model=self.llm,
            tools=[],  # No tools - direct JSON evaluation
            checkpointer=None,  # No LangGraph memory - use database instead
            state_modifier=self._get_system_prompt(),
        )

        logger.info(
            "MemoryEnhancedAnswerEvaluator initialized with agent (no checkpointer)"
        )

    def _get_system_prompt(self) -> str:
        """Get optimized system prompt for memory-enhanced evaluations with Week 3 JSON structure."""
        return ANSWER_EVALUATOR_SYSTEM_PROMPT

    async def evaluate_answer(
        self,
        session_id: str,
        question: str,
        user_answer: str,
        topic: str,
        difficulty: DifficultyLevel,
    ) -> AnswerEvaluation:
        """
        Evaluate user answer with state schema and conversation memory context.

        Week 2 Enhancement: State schema provides type-safe context and performance tracking.
        """
        logger.info(f"Evaluating answer with state schema for session {session_id}")

        # Get current state using schema
        state = await self.session_manager.get_session_state(session_id)
        if not state:
            logger.error(f"No state found for session {session_id}")
            return self._create_fallback_evaluation(user_answer, difficulty)

        # Get session config for memory access
        config = self.session_manager.get_config(session_id)

        # JSON-structured evaluation prompt with state schema context
        json_prompt = ANSWER_EVALUATION_PROMPT_TEMPLATE.format(
            session_id=state.interview_session_id,
            topic=state.current_topic,
            difficulty=state.difficulty_level,
            phase=state.interview_phase,
            question_count=state.question_count,
            evaluation_count=len(state.evaluation_history),
            has_performance_data=bool(state.user_performance),
            question=question,
            user_answer=user_answer,
            ready_for_summary=state.ready_for_summary,
        )

        try:
            # Get conversation history from database memory
            conversation_messages = (
                await self.session_manager.get_conversation_messages(session_id)
            )

            # Include conversation history plus current prompt for context
            messages = conversation_messages + [HumanMessage(content=json_prompt)]
            logger.info(f"messages for answer {conversation_messages}")
            # Single API call with full state context and database memory
            response = await self.agent.ainvoke(
                {
                    "messages": messages,
                    "interview_session_id": state.interview_session_id,
                    "current_topic": state.current_topic,
                    "difficulty_level": state.difficulty_level,
                    "interview_phase": state.interview_phase,
                    "question_count": state.question_count,
                    "evaluation_history": state.evaluation_history,
                    "user_performance": state.user_performance,
                }
            )
            logger.info(response)
            # Parse JSON response
            evaluation_data = self._parse_json_response(response)

            # Store evaluation in database as system message
            await self.session_manager.add_message_to_memory(
                session_id=session_id,
                role="SYSTEM",
                content=f"Answer evaluated - Score: {evaluation_data.get('overall_score', 'N/A')}",
                message_type="FEEDBACK",
                metadata={
                    "evaluation_type": "answer_evaluation",
                    "scores": evaluation_data.get("scores", {}),
                    "evaluation_data": evaluation_data,
                },
            )

            # Create structured evaluation object
            evaluation = self._create_evaluation_object(evaluation_data)

            # Update state with evaluation results
            state.evaluation_history.append(evaluation_data)

            # Update user performance tracking in state
            if not state.user_performance:
                state.user_performance = {}

            # Track performance metrics using state
            scores = evaluation_data.get("scores", {})
            avg_score = sum(scores.values()) / len(scores) if scores else 0

            performance_update = {
                "latest_score": avg_score,
                "evaluation_count": len(state.evaluation_history),
                "total_questions": state.question_count,
            }

            # Calculate trend if we have multiple evaluations
            if len(state.evaluation_history) > 1:
                prev_scores = state.evaluation_history[-2].get("scores", {})
                prev_avg = (
                    sum(prev_scores.values()) / len(prev_scores) if prev_scores else 0
                )
                performance_update["score_trend"] = (
                    "improving"
                    if avg_score > prev_avg
                    else "stable" if abs(avg_score - prev_avg) < 0.5 else "declining"
                )

            state.user_performance.update(performance_update)

            # Persist state updates
            await self.session_manager.update_session_state(
                session_id,
                {
                    "evaluation_history": state.evaluation_history,
                    "user_performance": state.user_performance,
                },
            )

            # Add evaluation to memory for cross-agent sharing
            await self.session_manager.add_evaluation_to_memory(
                session_id, evaluation_data
            )

            logger.info(
                f"Answer evaluated with state schema - Score: {avg_score:.1f}, Phase: {state.interview_phase}"
            )
            return evaluation

        except Exception as e:
            logger.error(f"Error evaluating answer with state schema: {e}")
            return self._create_fallback_evaluation(user_answer, difficulty)

    def _parse_json_response(self, response) -> Dict[str, Any]:
        """
        Simple JSON parsing - the AI already returns proper JSON format.
        """
        try:
            # Extract content from response
            content = self._extract_content_from_response(response)

            if not content:
                raise ValueError("No content found in response")

            # Simple approach: try markdown JSON first, then direct parsing
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end > start:
                    json_str = content[start:end].strip()
                    return json.loads(json_str)

            # Try direct parsing if no markdown blocks
            content = content.strip()
            if content.startswith("{") and content.endswith("}"):
                return json.loads(content)

            # Fallback: find JSON boundaries
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)

            raise ValueError("No valid JSON found in response")

        except Exception as e:
            logger.error(f"JSON parsing error: {e}")
            logger.debug(f"Content that failed to parse: {content[:200]}...")
            raise ValueError(f"Failed to parse evaluation JSON: {e}")

    def _extract_content_from_response(self, response) -> str:
        """Extract content string from various response formats."""
        if isinstance(response, dict) and "messages" in response:
            messages = response["messages"]
            for message in reversed(messages):
                if (
                    hasattr(message, "content")
                    and message.content
                    and message.content.strip()
                ):
                    return message.content
        elif hasattr(response, "content"):
            return response.content
        else:
            return str(response)
        return ""

    def _create_fallback_evaluation(
        self, user_answer: str, difficulty: DifficultyLevel
    ) -> AnswerEvaluation:
        """Create fallback evaluation when parsing fails."""
        logger.warning("Creating fallback evaluation")

        # Simple heuristic-based scoring for fallback
        answer_length = len(user_answer.split())
        base_score = min(7.0, max(3.0, answer_length / 20))  # Rough heuristic

        scores = EvaluationScores(
            clarity=base_score,
            technical_depth=base_score - 0.5,
            scalability_awareness=base_score - 1.0,
            trade_offs_understanding=base_score - 1.5,
        )

        analysis = AnswerAnalysis(
            strengths=["Engaged with the question", "Provided a response"],
            weaknesses=[
                "Could provide more technical detail",
                "Consider additional aspects",
            ],
            missing_topics=["Scalability considerations", "Performance implications"],
            technical_errors=[],
        )

        next_steps = NextSteps(
            needs_clarification=True,
            needs_deeper_dive=False,
            ready_for_next_topic=False,
            suggested_follow_up="clarification",
            specific_areas_to_explore=["Basic concepts", "Core requirements"],
        )

        return AnswerEvaluation(
            scores=scores,
            analysis=analysis,
            next_steps=next_steps,
            confidence_level=0.3,  # Low confidence for fallback
            evaluation_timestamp=datetime.now(),
        )

    def _create_evaluation_object(
        self, evaluation_data: Dict[str, Any]
    ) -> AnswerEvaluation:
        """Create structured AnswerEvaluation object from parsed data."""

        # Extract scores
        scores_data = evaluation_data.get("scores", {})
        scores = EvaluationScores(
            clarity=scores_data.get("clarity", 5.0),
            technical_depth=scores_data.get("technical_depth", 5.0),
            scalability_awareness=scores_data.get("scalability_awareness", 5.0),
            trade_offs_understanding=scores_data.get("trade_offs_understanding", 5.0),
        )

        # Extract analysis
        analysis_data = evaluation_data.get("analysis", {})
        analysis = AnswerAnalysis(
            strengths=analysis_data.get("strengths", []),
            weaknesses=analysis_data.get("weaknesses", []),
            missing_topics=analysis_data.get("missing_topics", []),
            technical_errors=analysis_data.get("technical_errors", []),
        )

        # Extract next steps
        next_steps_data = evaluation_data.get("next_steps", {})
        next_steps = NextSteps(
            needs_clarification=next_steps_data.get("needs_clarification", False),
            needs_deeper_dive=next_steps_data.get("needs_deeper_dive", True),
            ready_for_next_topic=next_steps_data.get("ready_for_next_topic", False),
            suggested_follow_up=next_steps_data.get(
                "suggested_follow_up", "deeper_dive"
            ),
            specific_areas_to_explore=next_steps_data.get(
                "specific_areas_to_explore", []
            ),
        )

        return AnswerEvaluation(
            scores=scores,
            analysis=analysis,
            next_steps=next_steps,
            confidence_level=evaluation_data.get("confidence_level", 0.8),
            evaluation_timestamp=datetime.now(),
        )

    def _create_fallback_evaluation(
        self, user_answer: str, difficulty: DifficultyLevel
    ) -> AnswerEvaluation:
        """Create fallback evaluation when parsing fails."""
        logger.warning("Creating fallback evaluation")

        # Simple heuristic-based scoring for fallback
        answer_length = len(user_answer.split())
        base_score = min(7.0, max(3.0, answer_length / 20))  # Rough heuristic

        scores = EvaluationScores(
            clarity=base_score,
            technical_depth=base_score - 0.5,
            scalability_awareness=base_score - 1.0,
            trade_offs_understanding=base_score - 1.5,
        )

        analysis = AnswerAnalysis(
            strengths=["Engaged with the question", "Provided a response"],
            weaknesses=[
                "Could provide more technical detail",
                "Consider additional aspects",
            ],
            missing_topics=["Scalability considerations", "Performance implications"],
            technical_errors=[],
        )

        next_steps = NextSteps(
            needs_clarification=False,
            needs_deeper_dive=True,
            ready_for_next_topic=False,
            suggested_follow_up="deeper_dive",
            specific_areas_to_explore=[
                "technical architecture",
                "scalability planning",
            ],
        )

        return AnswerEvaluation(
            scores=scores,
            analysis=analysis,
            next_steps=next_steps,
            confidence_level=0.6,  # Lower confidence for fallback
            evaluation_timestamp=datetime.now(),
        )
