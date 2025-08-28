"""
Difficulty Adaptor Agent
Simple agent for dynamically adjusting interview difficulty based on performance patterns
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser

from app.domain.entities.session import DifficultyLevel
from app.agents.models.output_schemas import DifficultyAdjustment
from app.infrastructure.config import settings
from app.shared.logging import get_logger

logger = get_logger(__name__)


class DifficultyAdaptorAgent:
    """
    Simple AI Agent for dynamically adapting interview difficulty based on performance patterns

    Uses direct LLM calls for intelligent analysis without complex workflows.
    Perfect for single-purpose operations with clear input/output patterns.

    Capabilities:
    - Analyze performance patterns to determine difficulty adjustments
    - Recommend when to increase or decrease challenge level
    - Maintain appropriate difficulty progression with clear reasoning
    - Balance challenge with achievability based on data-driven insights
    """

    def __init__(self):
        # Initialize OpenAI model for difficulty analysis
        self.llm = ChatOpenAI(
            model=settings.openai.model,
            temperature=0.3,  # Lower temperature for consistent recommendations
            api_key=settings.openai.api_key,
            max_tokens=1000,
        )

        # Create parser for structured difficulty adjustment responses
        self.parser = PydanticOutputParser(pydantic_object=DifficultyAdjustment)

        logger.info("DifficultyAdaptorAgent initialized with direct LLM approach")

    async def should_adjust_difficulty(
        self,
        performance_history: List[Dict[str, Any]],
        current_difficulty: DifficultyLevel,
        recent_confidence: float = 0.5,
    ) -> DifficultyAdjustment:
        """
        Determine if difficulty should be adjusted based on performance patterns

        Simple but intelligent analysis using direct LLM call with structured output

        Args:
            performance_history: List of recent performance evaluations
            current_difficulty: Current difficulty level
            recent_confidence: Most recent confidence level (0.0-1.0)

        Returns:
            Structured difficulty adjustment recommendation
        """
        logger.info(f"Analyzing difficulty adjustment from {current_difficulty}")

        try:
            # Create intelligent prompt for difficulty analysis
            prompt = f"""
            Analyze this performance history and determine if difficulty should be adjusted:
            
            **Current Difficulty:** {current_difficulty.value}
            **Recent Confidence Level:** {recent_confidence:.2f}
            
            **Performance History (most recent first):**
            {json.dumps(performance_history, indent=2)}
            
            **Analysis Criteria:**
            
            📈 **Increase Difficulty If:**
            - Consistent high scores (>8) across multiple attempts  
            - High confidence levels (>0.8) with detailed explanations
            - Candidate shows mastery of current level concepts
            - Proactive discussion of advanced topics and trade-offs
            - Quick resolution of problems with sophisticated reasoning
            
            📉 **Decrease Difficulty If:**
            - Consistent low scores (<4) across multiple attempts
            - Low confidence levels (<0.5) with struggle indicators
            - Missing fundamental concepts for current level
            - Repeated need for clarification on basic concepts  
            - Extended silences or confusion on standard questions
            
            🔄 **Maintain Current Level If:**
            - Scores in the 5-7 range showing appropriate challenge
            - Steady improvement trend over time
            - Good engagement with occasional struggles (healthy learning)
            - Appropriate depth for current difficulty level
            - Building confidence without being over/under-challenged
            
            **Decision Framework:**
            1. Look at the trend over the last 3-5 interactions
            2. Consider both average performance and consistency
            3. Factor in confidence levels and engagement quality
            4. Ensure adjustment serves learning objectives
            
            Provide structured recommendation using this format:
            {self.parser.get_format_instructions()}
            
            Be specific about the reasoning and provide clear confidence in your recommendation.
            """

            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            adjustment = self.parser.parse(response.content)

            logger.info(f"Difficulty analysis complete: {adjustment.adjustment_reason}")

            return adjustment

        except Exception as e:
            logger.error(f"Error in difficulty analysis: {str(e)}")
            # Return safe fallback
            return DifficultyAdjustment(
                current_difficulty=current_difficulty.value,
                recommended_difficulty=current_difficulty.value,
                adjustment_reason=f"Analysis error: {str(e)}",
                performance_trend="stable",
                confidence_in_recommendation=0.3,
                adjustment_needed=False,
            )

    async def analyze_performance_trend(
        self, performance_history: List[Dict[str, Any]], window_size: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze performance trends over recent interactions using simple LLM analysis

        Args:
            performance_history: List of recent performance evaluations
            window_size: Number of recent interactions to analyze

        Returns:
            Dict containing trend analysis with specific insights
        """
        logger.info(f"Analyzing performance trend over last {window_size} interactions")

        try:
            recent_performance = (
                performance_history[-window_size:] if performance_history else []
            )

            prompt = f"""
            Analyze the performance trend from this data to understand learning trajectory:
            
            **Performance Data (last {window_size} interactions):**
            {json.dumps(recent_performance, indent=2)}
            
            **Analysis Requirements:**
            
            🔍 **Trend Direction Analysis:**
            - Are scores generally improving, declining, or stable?
            - Is there consistency in the trend or erratic performance?
            - What's the momentum like - building or losing steam?
            
            📊 **Specific Patterns to Identify:**
            - **Improving**: Clear upward trend in scores and depth
            - **Declining**: Downward trend with decreasing engagement  
            - **Stable**: Consistent performance within reasonable range
            - **Inconsistent**: Erratic performance without clear pattern
            
            🎯 **Key Insights:**
            1. Areas showing clear improvement
            2. Areas showing concerning decline  
            3. Consistency of performance across different topics
            4. Confidence levels and engagement quality
            5. Learning velocity and adaptation to feedback
            
            Provide analysis as JSON with these exact fields:
            - "trend_direction": one of ["improving", "declining", "stable", "inconsistent"]
            - "momentum": one of ["strong", "moderate", "weak"]  
            - "consistency": one of ["high", "medium", "low"]
            - "areas_of_growth": [list of specific areas showing improvement]
            - "areas_of_concern": [list of areas showing decline or issues]
            - "overall_trajectory": "summary of where candidate is heading"
            - "confidence_trend": "how confidence levels are changing"
            - "learning_velocity": "how quickly they're adapting and learning"
            
            Be specific and data-driven in your analysis.
            """

            response = await self.llm.ainvoke([HumanMessage(content=prompt)])

            # Parse JSON response
            trend_analysis = self._parse_json_response(response.content)

            logger.info(
                f"Performance trend: {trend_analysis.get('trend_direction', 'unknown')}"
            )

            return trend_analysis

        except Exception as e:
            logger.error(f"Error analyzing performance trend: {str(e)}")
            return {
                "trend_direction": "stable",
                "momentum": "moderate",
                "consistency": "medium",
                "areas_of_growth": ["Continued participation"],
                "areas_of_concern": ["Analysis temporarily unavailable"],
                "overall_trajectory": "Continuing to engage with interview process",
                "confidence_trend": "Maintaining engagement",
                "learning_velocity": "Steady progress",
                "error": str(e),
            }

    async def get_difficulty_recommendation(
        self,
        current_performance: Dict[str, Any],
        topic: str,
        session_progress: Dict[str, Any],
    ) -> str:
        """
        Get a specific difficulty recommendation with reasoning for current context

        Args:
            current_performance: Most recent performance metrics
            topic: Current topic being discussed
            session_progress: Overall session progress data

        Returns:
            Detailed recommendation string with actionable guidance
        """
        logger.info(f"Generating difficulty recommendation for {topic}")

        try:
            prompt = f"""
            Provide a specific difficulty recommendation for this interview context:
            
            **Current Performance:**
            {json.dumps(current_performance, indent=2)}
            
            **Topic:** {topic}
            **Session Progress:** {json.dumps(session_progress, indent=2)}
            
            **Generate Recommendation:**
            
            Based on the current performance and context, provide specific guidance on:
            
            1. **Immediate Difficulty Decision:** 
               - Should we increase, decrease, or maintain current difficulty?
               - What specific changes should be made to question complexity?
            
            2. **Topic-Specific Considerations:**
               - How does performance on {topic} inform difficulty choices?
               - Are there topic-specific factors affecting performance?
            
            3. **Actionable Next Steps:**
               - What specific approach should the interviewer take?
               - How should questions be framed for optimal challenge?
               - What support or scaffolding might be needed?
            
            4. **Timing Considerations:**
               - When should any adjustments be implemented?
               - How quickly should difficulty changes be made?
            
            Provide a clear, actionable recommendation that an interviewer can immediately implement.
            Be specific about what to do, not just what the performance indicates.
            """

            response = await self.llm.ainvoke([HumanMessage(content=prompt)])

            recommendation = response.content

            logger.info("Difficulty recommendation generated successfully")

            return recommendation

        except Exception as e:
            logger.error(f"Error generating difficulty recommendation: {str(e)}")
            return f"""
            **Difficulty Recommendation (Fallback):**
            
            Based on available data, continue with current difficulty level while monitoring:
            - Candidate engagement and confidence
            - Quality of responses to current questions
            - Signs of being over or under-challenged
            
            Adjust gradually based on clear performance patterns.
            
            *Note: Full analysis temporarily unavailable due to: {str(e)}*
            """

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response with error handling"""
        try:
            # Extract JSON from response if wrapped in markdown
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.rfind("```")
                response = response[start:end].strip()

            return json.loads(response)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            return {
                "trend_direction": "stable",
                "momentum": "moderate",
                "consistency": "medium",
                "areas_of_growth": ["Parsing error occurred"],
                "areas_of_concern": ["Response format issues"],
                "overall_trajectory": "Unable to determine due to parsing error",
                "error": f"JSON parsing failed: {str(e)}",
            }

    def _calculate_average_score(self, performance_data: Dict[str, Any]) -> float:
        """Calculate average performance score from evaluation data"""
        scores = []

        # Try different possible score structures
        if "scores" in performance_data:
            score_obj = performance_data["scores"]
            if hasattr(score_obj, "__dict__"):
                for attr in [
                    "clarity",
                    "technical_depth",
                    "scalability_awareness",
                    "trade_offs_understanding",
                ]:
                    if hasattr(score_obj, attr):
                        scores.append(getattr(score_obj, attr))
            elif isinstance(score_obj, dict):
                for field in [
                    "clarity",
                    "technical_depth",
                    "scalability_awareness",
                    "trade_offs_understanding",
                ]:
                    if field in score_obj:
                        scores.append(score_obj[field])

        # Try direct field access
        for field in [
            "clarity_score",
            "technical_depth",
            "scalability_awareness",
            "trade_offs_understanding",
        ]:
            if field in performance_data and performance_data[field] is not None:
                scores.append(performance_data[field])

        return sum(scores) / len(scores) if scores else 5.0
