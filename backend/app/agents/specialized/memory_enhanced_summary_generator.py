"""
Memory-Enhanced Summary Generator Agent - Week 4 Implementation
Single API call summary generation with c            # Get performance summary for agent context
            performance_summary = await self.session_manager.get_performance_summary(session_id)

            # Single API call with comprehensive state context
            response = await self.agent.ainvoke(
                {
                    "messages": messages,
                    "interview_session_id": state.interview_session_id,
                    "current_topic": state.current_topic,
                    "difficulty_level": state.difficulty_level,
                    "interview_phase": state.interview_phase,
                    "question_count": state.question_count,
                    "evaluation_history": state.evaluation_history,
                    "performance_summary": performance_summary,
                    "topics_covered": state.topics_covered,
                }rsation analysis
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from app.domain.entities.session import DifficultyLevel
from app.agents.models.output_schemas import (
    InterviewSummary,
    PerformanceAnalysis,
    LearningAssessment,
    RecommendationSet,
)
from app.agents.memory.memory_enhanced_session_manager import (
    MemoryEnhancedSessionManager,
)
from app.infrastructure.config.settings import get_settings
from app.agents.prompts import (
    SUMMARY_GENERATOR_SYSTEM_PROMPT,
    SUMMARY_GENERATOR_SUMMARY_TEMPLATE,
)
from app.shared.logging import get_logger

logger = get_logger(__name__)


class MemoryEnhancedSummaryGenerator:
    """
    Memory-Enhanced Summary Generator with database memory and complete conversation analysis.

    Features:
    - Uses LangGraph agent pattern with database memory (no checkpointer)
    - Single API call summary generation
    - Complete conversation memory access via database
    - Performance trend analysis with rich interview context
    - Learning progression assessment
    - Actionable next steps recommendations
    - JSON-structured comprehensive summaries
    """

    def __init__(self, session_manager: MemoryEnhancedSessionManager):
        self.settings = get_settings()
        self.session_manager = session_manager

        # Initialize OpenAI model with optimized settings for comprehensive analysis
        self.llm = ChatOpenAI(
            model=self.settings.openai.model,
            temperature=0.1,  # Very low temperature for consistent, analytical summaries
            api_key=self.settings.openai.api_key,
            max_tokens=2000,  # Increased for comprehensive summaries
        )

        # Create React agent WITHOUT checkpointer - we handle memory via database
        self.agent = create_react_agent(
            model=self.llm,
            tools=[],  # No tools - direct JSON summary generation
            checkpointer=None,  # No LangGraph memory - use database instead
            state_modifier=self._get_system_prompt(),
        )

        logger.info(
            "MemoryEnhancedSummaryGenerator initialized with agent (no checkpointer)"
        )

    def _get_system_prompt(self) -> str:
        """Get system prompt for comprehensive interview summary generation."""
        return SUMMARY_GENERATOR_SYSTEM_PROMPT

    async def generate_interview_summary(
        self, session_id: str, difficulty_level: DifficultyLevel
    ) -> InterviewSummary:
        """
        Week 4: Generate comprehensive interview summary with complete conversation analysis.

        Single API call leveraging full conversation memory for holistic assessment.
        """
        try:
            # Get current state with complete history
            state = await self.session_manager.get_session_state(session_id)

            # Create comprehensive analysis prompt with full context
            summary_prompt = SUMMARY_GENERATOR_SUMMARY_TEMPLATE.format(
                session_id=session_id,
                difficulty_level=difficulty_level.value,
                question_count=state.question_count,
                interview_phase=state.interview_phase,
                topics_covered=", ".join(state.topics_covered),
                evaluation_count=len(state.evaluation_history),
                performance_summary=await self.session_manager.get_performance_summary(
                    session_id
                ),
                evaluation_history_summary=self._format_evaluation_history_summary(
                    state.evaluation_history
                ),
            )

            summary_prompt += "\n\nRespond with the exact JSON structure specified in your instructions."

            # Get conversation history from database memory
            conversation_messages = (
                await self.session_manager.get_conversation_messages(session_id)
            )

            # Include conversation history plus current prompt for context
            messages = conversation_messages + [HumanMessage(content=summary_prompt)]

            # Get performance summary for agent context
            performance_summary = await self.session_manager.get_performance_summary(
                session_id
            )

            # Single API call with complete state context and database memory
            response = await self.agent.ainvoke(
                {
                    "messages": messages,
                    "interview_session_id": state.interview_session_id,
                    "current_topic": state.current_topic,
                    "difficulty_level": state.difficulty_level,
                    "interview_phase": state.interview_phase,
                    "question_count": state.question_count,
                    "evaluation_history": state.evaluation_history,
                    "performance_summary": performance_summary,
                    "topics_covered": state.topics_covered,
                }
            )

            # Parse comprehensive summary from response
            summary_data = self._parse_json_response(response)

            # Create structured InterviewSummary object
            interview_summary = self._create_summary_object(
                summary_data, difficulty_level
            )

            # Update session state with summary
            await self.session_manager.update_session_state(
                session_id,
                {
                    "interview_summary": interview_summary,
                    "summary_generated": True,
                    "summary_timestamp": datetime.now(),
                },
            )

            logger.info(
                f"Week 4 comprehensive summary generated for session {session_id}"
            )
            return interview_summary

        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            # Return fallback summary if generation fails
            return self._create_fallback_summary(session_id, difficulty_level)

    def _format_evaluation_history_summary(self, evaluation_history: List[Dict]) -> str:
        """Format evaluation history for context prompt."""
        if not evaluation_history:
            return "No evaluations completed yet."

        summary_lines = []
        for i, eval_data in enumerate(evaluation_history[-5:], 1):  # Last 5 evaluations
            scores = eval_data.get("scores", {})
            avg_score = sum(scores.values()) / len(scores) if scores else 0
            summary_lines.append(
                f"Evaluation {i}: Avg Score {avg_score:.1f} - {eval_data.get('analysis', {}).get('strengths', ['Good effort'])[0] if eval_data.get('analysis') else 'No analysis'}"
            )

        return "\n".join(summary_lines)

    def _parse_json_response(self, response) -> Dict[str, Any]:
        """
        Parse comprehensive summary JSON with enhanced error handling.
        """
        try:
            # Extract content from response
            content = self._extract_content_from_response(response)

            if not content:
                raise ValueError("No content found in response")

            # Use similar parsing strategies as other Week 3 enhanced agents
            parsing_strategies = [
                self._parse_clean_json,
                self._parse_markdown_json,
                self._parse_bounded_json,
                self._parse_with_fixes,
            ]

            last_error = None
            for strategy in parsing_strategies:
                try:
                    summary_data = strategy(content)
                    if summary_data:
                        # Validate summary structure
                        self._validate_summary_structure(summary_data)
                        logger.debug(
                            f"Successfully parsed summary with strategy: {strategy.__name__}"
                        )
                        return summary_data
                except Exception as e:
                    last_error = e
                    continue

            # If all strategies fail, raise the last error
            raise last_error or ValueError("All parsing strategies failed")

        except Exception as e:
            logger.error(f"Summary JSON parsing error: {e}")
            logger.debug(f"Content that failed to parse: {content[:200]}...")
            raise ValueError(f"Failed to parse summary JSON: {e}")

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

    def _parse_clean_json(self, content: str) -> Dict[str, Any]:
        """Try parsing content directly as JSON."""
        content = content.strip()
        if content.startswith("{") and content.endswith("}"):
            return json.loads(content)
        raise ValueError("Not clean JSON format")

    def _parse_markdown_json(self, content: str) -> Dict[str, Any]:
        """Extract JSON from markdown code blocks."""
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end > start:
                json_str = content[start:end].strip()
                return json.loads(json_str)
        elif "```" in content:
            # Try any code block
            start = content.find("```") + 3
            end = content.find("```", start)
            if end > start:
                json_str = content[start:end].strip()
                # Skip language identifier line if present
                lines = json_str.split("\n")
                if lines and not lines[0].strip().startswith("{"):
                    json_str = "\n".join(lines[1:])
                return json.loads(json_str)
        raise ValueError("No markdown JSON found")

    def _parse_bounded_json(self, content: str) -> Dict[str, Any]:
        """Find JSON object boundaries and extract."""
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = content[start:end]
            return json.loads(json_str)
        raise ValueError("No JSON boundaries found")

    def _parse_with_fixes(self, content: str) -> Dict[str, Any]:
        """Try parsing with common JSON fixes applied."""
        json_str = self._extract_json_content(content)
        if json_str:
            fixed_json = self._fix_common_json_issues(json_str)
            return json.loads(fixed_json)
        raise ValueError("Could not extract or fix JSON")

    def _extract_json_content(self, content: str) -> str:
        """Extract the most likely JSON content from response."""
        # Find largest JSON-like block
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            return content[start:end]
        return ""

    def _fix_common_json_issues(self, json_str: str) -> str:
        """Fix common JSON formatting issues."""
        import re

        fixes = [
            # Fix trailing commas
            (r",(\s*[}\]])", r"\1"),
            # Fix missing commas between objects
            (r'"\s*\n\s*"', '",\n  "'),
            # Fix boolean values
            (r':\s*"(true|false)"', r": \1"),
            # Fix number values in quotes
            (r':\s*"(\d+\.?\d*)"', r": \1"),
        ]

        fixed_json = json_str
        for pattern, replacement in fixes:
            fixed_json = re.sub(pattern, replacement, fixed_json)

        return fixed_json

    def _validate_summary_structure(self, data: Dict[str, Any]):
        """Validate comprehensive summary structure."""
        required_sections = [
            "overall_performance",
            "performance_progression",
            "technical_assessment",
            "learning_demonstration",
            "interview_flow_analysis",
            "recommendations",
            "notable_highlights",
            "session_metadata",
        ]

        for section in required_sections:
            if section not in data:
                logger.warning(f"Missing required summary section: {section}")
                data[section] = self._get_default_summary_section(section)

    def _get_default_summary_section(self, section: str) -> Dict[str, Any]:
        """Get default structure for missing summary sections."""
        defaults = {
            "overall_performance": {
                "final_score": 6.0,
                "performance_level": "intermediate",
                "readiness_for_next_level": False,
                "strongest_areas": ["engagement", "communication"],
                "improvement_areas": ["technical depth", "implementation details"],
            },
            "performance_progression": {
                "starting_level": "beginner",
                "ending_level": "intermediate",
                "improvement_trajectory": "steady",
                "breakthrough_moments": ["engaged well with questions"],
                "struggle_points": ["needed more technical detail"],
            },
            "technical_assessment": {
                "architecture_design": 6.0,
                "scalability_thinking": 6.0,
                "technology_choices": 6.0,
                "trade_off_analysis": 5.0,
                "implementation_details": 5.0,
                "communication_clarity": 7.0,
            },
            "learning_demonstration": {
                "concepts_learned": ["system design basics"],
                "knowledge_applied": ["general programming experience"],
                "adaptability_shown": True,
                "feedback_incorporation": "good",
                "curiosity_level": "moderate",
            },
            "interview_flow_analysis": {
                "engagement_quality": "good",
                "question_handling": "adequate",
                "clarification_seeking": "appropriate",
                "time_management": "good",
                "communication_style": "clear",
            },
            "recommendations": {
                "immediate_focus": ["practice system design problems"],
                "study_areas": ["scalability patterns", "architecture design"],
                "practice_suggestions": ["mock interviews"],
                "next_difficulty_readiness": "ready with more practice",
                "specific_resources": ["system design primer"],
            },
            "notable_highlights": ["Good engagement and willingness to learn"],
            "session_metadata": {
                "total_questions": 0,
                "session_duration_minutes": 30,
                "difficulty_level": "intermediate",
                "topics_covered": [],
                "completion_status": "incomplete",
            },
        }
        return defaults.get(section, {})

    def _create_summary_object(
        self, summary_data: Dict[str, Any], difficulty: DifficultyLevel
    ) -> InterviewSummary:
        """Create structured InterviewSummary object from parsed data."""

        # Extract performance analysis
        overall_perf = summary_data.get("overall_performance", {})
        perf_progression = summary_data.get("performance_progression", {})
        tech_assessment = summary_data.get("technical_assessment", {})

        performance_analysis = PerformanceAnalysis(
            final_score=overall_perf.get("final_score", 6.0),
            performance_level=overall_perf.get("performance_level", "intermediate"),
            strongest_areas=overall_perf.get("strongest_areas", []),
            improvement_areas=overall_perf.get("improvement_areas", []),
            technical_scores=tech_assessment,
            progression_trajectory=perf_progression.get(
                "improvement_trajectory", "steady"
            ),
        )

        # Extract learning assessment
        learning_demo = summary_data.get("learning_demonstration", {})
        learning_assessment = LearningAssessment(
            concepts_learned=learning_demo.get("concepts_learned", []),
            knowledge_applied=learning_demo.get("knowledge_applied", []),
            adaptability_shown=learning_demo.get("adaptability_shown", True),
            feedback_incorporation=learning_demo.get("feedback_incorporation", "good"),
            curiosity_level=learning_demo.get("curiosity_level", "moderate"),
        )

        # Extract recommendations
        recommendations_data = summary_data.get("recommendations", {})
        recommendations = RecommendationSet(
            immediate_focus=recommendations_data.get("immediate_focus", []),
            study_areas=recommendations_data.get("study_areas", []),
            practice_suggestions=recommendations_data.get("practice_suggestions", []),
            next_difficulty_readiness=recommendations_data.get(
                "next_difficulty_readiness", "needs more practice"
            ),
            specific_resources=recommendations_data.get("specific_resources", []),
        )

        return InterviewSummary(
            performance_analysis=performance_analysis,
            learning_assessment=learning_assessment,
            recommendations=recommendations,
            notable_highlights=summary_data.get("notable_highlights", []),
            session_metadata=summary_data.get("session_metadata", {}),
            readiness_for_next_level=overall_perf.get(
                "readiness_for_next_level", False
            ),
            summary_timestamp=datetime.now(),
        )

    def _create_fallback_summary(
        self, session_id: str, difficulty: DifficultyLevel
    ) -> InterviewSummary:
        """Create fallback summary when generation fails."""
        logger.warning(f"Creating fallback summary for session {session_id}")

        performance_analysis = PerformanceAnalysis(
            final_score=6.0,
            performance_level="intermediate",
            strongest_areas=["engagement", "communication"],
            improvement_areas=["technical detail", "implementation specifics"],
            technical_scores={
                "architecture_design": 6.0,
                "scalability_thinking": 6.0,
                "technology_choices": 6.0,
                "trade_off_analysis": 5.0,
                "implementation_details": 5.0,
                "communication_clarity": 7.0,
            },
            progression_trajectory="steady",
        )

        learning_assessment = LearningAssessment(
            concepts_learned=["system design basics"],
            knowledge_applied=["general programming knowledge"],
            adaptability_shown=True,
            feedback_incorporation="good",
            curiosity_level="moderate",
        )

        recommendations = RecommendationSet(
            immediate_focus=["practice system design scenarios"],
            study_areas=["scalability patterns", "system architecture"],
            practice_suggestions=["mock interviews", "design exercises"],
            next_difficulty_readiness="ready with additional practice",
            specific_resources=["system design primer", "architecture guides"],
        )

        return InterviewSummary(
            performance_analysis=performance_analysis,
            learning_assessment=learning_assessment,
            recommendations=recommendations,
            notable_highlights=[
                "Engaged well with questions",
                "Good communication skills",
            ],
            session_metadata={
                "total_questions": 0,
                "session_duration_minutes": 30,
                "difficulty_level": difficulty.value,
                "topics_covered": [],
                "completion_status": "fallback_summary",
            },
            readiness_for_next_level=False,
            summary_timestamp=datetime.now(),
        )
