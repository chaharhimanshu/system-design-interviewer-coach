"""
Pydantic Models for AI Agent Structured Outputs
"""

from datetime import datetime
from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field


class EvaluationScores(BaseModel):
    """Structured scores for answer evaluation"""

    clarity: float = Field(
        ge=0, le=10, description="Clarity and structure of explanation"
    )
    technical_depth: float = Field(
        ge=0, le=10, description="Technical depth and accuracy"
    )
    scalability_awareness: float = Field(
        ge=0, le=10, description="Understanding of scalability"
    )
    trade_offs_understanding: float = Field(
        ge=0, le=10, description="Discussion of trade-offs"
    )

    @property
    def average_score(self) -> float:
        return (
            self.clarity
            + self.technical_depth
            + self.scalability_awareness
            + self.trade_offs_understanding
        ) / 4


class AnswerAnalysis(BaseModel):
    """Detailed analysis of the answer"""

    strengths: List[str] = Field(description="What was done well in the answer")
    weaknesses: List[str] = Field(description="Areas that need improvement")
    missing_topics: List[str] = Field(description="Important topics not addressed")
    technical_errors: List[str] = Field(description="Technical inaccuracies identified")


class NextSteps(BaseModel):
    """Recommendations for next steps in interview"""

    needs_clarification: bool = Field(description="Whether answer needs clarification")
    needs_deeper_dive: bool = Field(description="Should dig deeper on current topic")
    ready_for_next_topic: bool = Field(description="Ready to move to next area")
    suggested_follow_up: Literal[
        "clarification", "deeper_dive", "next_topic", "feedback"
    ] = Field(description="Recommended follow-up approach")
    specific_areas_to_explore: List[str] = Field(
        description="Specific areas or questions to explore next"
    )


class AnswerEvaluation(BaseModel):
    """Complete answer evaluation output"""

    scores: EvaluationScores
    analysis: AnswerAnalysis
    next_steps: NextSteps
    evaluation_timestamp: datetime = Field(default_factory=datetime.now)
    confidence_level: float = Field(
        ge=0, le=1, description="Evaluator's confidence in assessment"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class QuestionGeneration(BaseModel):
    """Generated question with context"""

    question: str = Field(description="The interview question")
    question_type: Literal[
        "opening", "follow_up", "clarification", "topic_transition"
    ] = Field(description="Type of question being asked")
    topics_targeted: List[str] = Field(
        description="Topics this question aims to explore"
    )
    difficulty_level: Literal["beginner", "intermediate", "advanced"] = Field(
        description="Difficulty level of the question"
    )
    expected_concepts: List[str] = Field(
        description="Concepts candidate should ideally discuss"
    )
    guidance_hints: List[str] = Field(
        description="Hints available if candidate struggles"
    )


class FeedbackResponse(BaseModel):
    """Comprehensive structured feedback response"""

    # Executive Summary
    executive_summary: str = Field(description="Overall performance assessment summary")
    overall_recommendation: str = Field(description="Overall recommendation or grade")

    # Performance Analysis
    performance_analysis: Dict[str, Any] = Field(
        description="Detailed performance breakdown"
    )
    technical_knowledge_score: float = Field(
        ge=0, le=10, description="Technical knowledge demonstration"
    )
    problem_solving_score: float = Field(
        ge=0, le=10, description="Problem-solving effectiveness"
    )
    communication_score: float = Field(
        ge=0, le=10, description="Communication clarity and structure"
    )
    architecture_design_score: float = Field(
        ge=0, le=10, description="Architectural thinking quality"
    )

    # Architecture Comparison
    architecture_insights: Dict[str, Any] = Field(
        description="Architecture comparison and insights"
    )
    user_proposed_architecture: Dict[str, Any] = Field(
        description="User's proposed solution"
    )
    expected_architecture: Dict[str, Any] = Field(
        description="Expected solution based on standards"
    )
    compliance_score: float = Field(
        ge=0, le=100, description="Organizational standard alignment percentage"
    )
    critical_gaps: List[str] = Field(description="Critical gaps in their design")
    architectural_improvements: List[str] = Field(
        description="Specific architectural improvements"
    )

    # Learning and Development
    learning_roadmap: Dict[str, List[str]] = Field(
        description="Structured learning recommendations"
    )
    immediate_focus_areas: List[str] = Field(
        description="What to focus on in next 1-2 weeks"
    )
    medium_term_goals: List[str] = Field(description="Learning goals for 1-3 months")
    long_term_development: List[str] = Field(
        description="Development areas for 3+ months"
    )

    # Specific Feedback
    key_strengths: List[str] = Field(description="Primary strengths demonstrated")
    improvement_areas: List[str] = Field(
        description="Areas needing improvement with specifics"
    )
    technical_corrections: List[str] = Field(
        description="Technical errors that need correction"
    )
    missing_concepts: List[str] = Field(description="Important concepts not addressed")

    # Next Steps
    next_interview_preparation: Dict[str, Any] = Field(
        description="How to prepare for future interviews"
    )
    practice_recommendations: List[str] = Field(
        description="Specific practice suggestions"
    )
    resource_suggestions: List[str] = Field(
        description="Learning resources and materials"
    )

    # Encouragement and Motivation
    encouragement_message: str = Field(description="Personalized motivational message")
    growth_recognition: str = Field(description="Recognition of effort and progress")
    confidence_building_notes: List[str] = Field(
        description="Confidence building observations"
    )

    # Visual Elements
    ascii_diagrams: Dict[str, str] = Field(
        description="ASCII diagrams for architecture comparison", default={}
    )
    comparison_charts: Dict[str, Any] = Field(
        description="Performance comparison data", default={}
    )

    # Metadata
    feedback_style_used: str = Field(description="Feedback style applied")
    generated_at: datetime = Field(default_factory=datetime.now)
    comprehensive_analysis: bool = Field(
        default=True, description="Whether this is comprehensive feedback"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class DifficultyAdjustment(BaseModel):
    """Difficulty adjustment recommendation"""

    current_difficulty: Literal["beginner", "intermediate", "advanced"]
    recommended_difficulty: Literal["beginner", "intermediate", "advanced"]
    adjustment_reason: str = Field(description="Reason for difficulty adjustment")
    performance_trend: Literal["improving", "stable", "declining"] = Field(
        description="Observed performance trend"
    )
    confidence_in_recommendation: float = Field(
        ge=0, le=1, description="Confidence in adjustment recommendation"
    )
    adjustment_needed: bool = Field(description="Whether adjustment is needed")


class ConversationInsights(BaseModel):
    """Insights about the overall conversation"""

    coverage_completeness: float = Field(
        ge=0, le=100, description="Percentage of topic coverage"
    )
    progression_quality: float = Field(
        ge=0, le=10, description="Quality of conversation flow"
    )
    candidate_growth_indicators: List[str] = Field(
        description="Signs of learning during interview"
    )
    recommended_focus_areas: List[str] = Field(description="Areas to focus on next")
    estimated_completion_percentage: float = Field(
        ge=0, le=100, description="Estimated completion percentage"
    )
    key_achievements: List[str] = Field(
        description="Key achievements in the conversation"
    )
    remaining_critical_topics: List[str] = Field(
        description="Critical topics still to be covered"
    )


class AIHint(BaseModel):
    """AI-generated hint for candidate"""

    hint_type: Literal["conceptual", "technical", "approach", "example"] = Field(
        description="Type of hint being provided"
    )
    hint_content: str = Field(description="The actual hint content")
    reasoning: str = Field(description="Why this hint is relevant")
    follow_up_questions: List[str] = Field(
        description="Questions candidate should consider after the hint"
    )


class SessionSummary(BaseModel):
    """Complete session summary"""

    overall_performance: EvaluationScores
    topic_coverage: Dict[str, float] = Field(
        description="Coverage percentage for each topic area"
    )
    key_strengths: List[str] = Field(description="Primary strengths demonstrated")
    primary_growth_areas: List[str] = Field(description="Main areas for improvement")
    learning_progression: List[str] = Field(
        description="How candidate progressed during session"
    )
    recommended_next_steps: List[str] = Field(
        description="Recommended actions for continued learning"
    )
    session_highlights: List[str] = Field(
        description="Notable moments or insights from session"
    )
    readiness_assessment: Dict[str, str] = Field(
        description="Assessment of readiness for different interview levels"
    )
