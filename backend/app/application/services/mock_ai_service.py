"""
Mock AI Service for Development and Testing
Replaces real OpenAI calls with predefined responses for faster development
"""

import asyncio
import random
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime

from app.agents.models.output_schemas import (
    AnswerEvaluation,
    QuestionGeneration,
    FeedbackResponse,
    AIHint,
    SessionSummary,
    ConversationInsights,
    EvaluationScores,
    AnswerAnalysis,
    NextSteps,
)


class MockAIService:
    """Mock AI service that returns realistic but fake responses"""

    def __init__(self):
        self.response_delay = 0.5  # Simulate AI processing time

    async def _simulate_processing(self):
        """Simulate AI processing delay"""
        await asyncio.sleep(self.response_delay + random.uniform(0.1, 1.0))

    async def generate_interview_question(
        self, topic: str, difficulty: str, context: Dict[str, Any] = None
    ) -> QuestionGeneration:
        """Mock question generation"""
        await self._simulate_processing()

        questions = {
            "url_shortener": [
                "Let's start with the basics. Can you walk me through what a URL shortener does and what the main requirements would be?",
                "Great! Now let's think about scale. How would you handle 100 million URLs being shortened per day?",
                "How would you design the database schema for storing the URLs and their mappings?",
                "What strategies would you use to generate the short codes? What are the trade-offs?",
            ],
            "chat_system": [
                "Design a real-time chat system like WhatsApp. What are the core components you'd need?",
                "How would you handle message delivery and ensure messages aren't lost?",
                "How would you implement presence indicators (online/offline status)?",
                "How would you handle group chats with thousands of participants?",
            ],
        }

        topic_key = "url_shortener" if "url" in topic.lower() else "chat_system"
        question_text = random.choice(
            questions.get(topic_key, questions["url_shortener"])
        )

        return QuestionGeneration(
            question_text=question_text,
            question_type="technical_deep_dive",
            difficulty_level=difficulty,
            expected_topics=[
                "System architecture",
                "Database design",
                "Scalability",
                "Load balancing",
            ],
            follow_up_areas=[
                "Caching strategies",
                "Database sharding",
                "API design",
                "Security considerations",
            ],
            time_estimate_minutes=15,
            hints=[
                "Think about the read vs write ratio",
                "Consider using a NoSQL database for scale",
                "Think about cache-aside pattern",
            ],
        )

    async def evaluate_answer(
        self, question: str, answer: str, context: Dict[str, Any] = None
    ) -> AnswerEvaluation:
        """Mock answer evaluation"""
        await self._simulate_processing()

        # Simulate realistic scores based on answer length and keywords
        answer_length = len(answer.split())
        has_technical_terms = any(
            term in answer.lower()
            for term in [
                "database",
                "cache",
                "load balancer",
                "microservice",
                "api",
                "scalability",
                "redis",
                "postgresql",
                "nginx",
            ]
        )

        technical_score = min(
            90, 40 + answer_length * 2 + (30 if has_technical_terms else 0)
        )
        clarity_score = min(95, 50 + answer_length * 1.5)
        completeness_score = min(85, 30 + answer_length * 3)

        return AnswerEvaluation(
            overall_score=int(
                (technical_score + clarity_score + completeness_score) / 3
            ),
            scores=EvaluationScores(
                technical_accuracy=technical_score,
                clarity_and_communication=clarity_score,
                completeness=completeness_score,
                scalability_awareness=random.randint(70, 90),
                trade_off_analysis=random.randint(60, 85),
            ),
            analysis=AnswerAnalysis(
                strengths=[
                    "Good understanding of basic concepts",
                    "Clear explanation of the approach",
                    "Consideration of scalability factors",
                ],
                weaknesses=[
                    "Could elaborate more on database design",
                    "Missing discussion of caching strategies",
                    "Could consider edge cases better",
                ],
                missing_topics=[
                    "Load balancing strategies",
                    "Database indexing",
                    "Monitoring and alerting",
                ],
                technical_gaps=[
                    "CAP theorem implications",
                    "Consistency models",
                    "Failure handling",
                ],
            ),
            next_steps=NextSteps(
                recommended_follow_ups=[
                    "Let's dive deeper into the database design",
                    "How would you handle caching in this system?",
                    "What monitoring would you implement?",
                ],
                difficulty_adjustment="maintain",
                focus_areas=[
                    "Database optimization",
                    "Caching strategies",
                    "System monitoring",
                ],
            ),
            confidence_level=random.uniform(0.75, 0.95),
        )

    async def generate_hint(
        self,
        current_question: str,
        conversation_context: List[Dict[str, Any]],
        difficulty: str,
    ) -> AIHint:
        """Mock hint generation"""
        await self._simulate_processing()

        hints = [
            "Think about the read-to-write ratio in this system. URL shorteners typically have much more reads than writes.",
            "Consider using a hash function or base62 encoding for generating short codes.",
            "What happens when your database becomes the bottleneck? Think about read replicas and caching.",
            "How would you handle analytics? You'll need to track clicks without impacting performance.",
            "Think about the geographic distribution of your users. CDN and regional databases could help.",
        ]

        return AIHint(
            hint_text=random.choice(hints),
            hint_type="guided_question",
            difficulty_level=difficulty,
            related_concepts=[
                "Database design",
                "Caching strategies",
                "Load balancing",
                "System architecture",
            ],
            next_steps=[
                "Consider how this affects your overall architecture",
                "Think about the trade-offs of different approaches",
                "Consider the impact on system performance",
            ],
        )

    async def generate_feedback(
        self, session_data: Dict[str, Any], conversation_history: List[Dict[str, Any]]
    ) -> FeedbackResponse:
        """Mock comprehensive feedback"""
        await self._simulate_processing()

        return FeedbackResponse(
            overall_rating=random.randint(70, 90),
            detailed_scores={
                "technical_depth": random.randint(75, 95),
                "problem_solving": random.randint(70, 90),
                "communication": random.randint(80, 95),
                "system_thinking": random.randint(65, 85),
            },
            strengths=[
                "Strong understanding of database fundamentals",
                "Good consideration of scalability challenges",
                "Clear communication of technical concepts",
                "Thoughtful approach to trade-off analysis",
            ],
            areas_for_improvement=[
                "Could explore more caching strategies",
                "Consider discussing monitoring and observability",
                "Think about failure scenarios and recovery",
                "Could elaborate on security considerations",
            ],
            specific_feedback={
                "architecture": "Your high-level architecture is solid. Consider adding more detail about service boundaries.",
                "database": "Good choice of database technology. Think about partitioning strategies for scale.",
                "caching": "You mentioned caching briefly. This is crucial for URL shorteners - elaborate more.",
                "apis": "Your API design is reasonable. Consider rate limiting and authentication.",
            },
            recommendations=[
                "Practice more distributed systems problems",
                "Study caching patterns in depth",
                "Learn about database sharding strategies",
                "Explore monitoring and alerting best practices",
            ],
            performance_trends={
                "technical_accuracy": "improving",
                "communication": "strong",
                "completeness": "needs_work",
            },
            generated_at=datetime.now(),
        )

    async def generate_session_summary(
        self, session_data: Dict[str, Any], conversation_history: List[Dict[str, Any]]
    ) -> SessionSummary:
        """Mock session summary"""
        await self._simulate_processing()

        return SessionSummary(
            session_id=str(session_data.get("session_id", "mock-session")),
            topic=session_data.get("topic", "System Design"),
            duration_minutes=session_data.get("duration", 45),
            total_questions=len(
                [msg for msg in conversation_history if msg.get("role") == "assistant"]
            ),
            total_responses=len(
                [msg for msg in conversation_history if msg.get("role") == "user"]
            ),
            overall_performance=random.randint(70, 90),
            key_topics_covered=[
                "System architecture",
                "Database design",
                "Scalability planning",
                "API design",
                "Caching strategies",
            ],
            performance_by_area={
                "technical_depth": random.randint(75, 90),
                "communication": random.randint(80, 95),
                "problem_solving": random.randint(70, 85),
                "scalability_thinking": random.randint(65, 80),
            },
            strengths=[
                "Strong foundational knowledge",
                "Good problem decomposition",
                "Clear communication style",
            ],
            improvement_areas=[
                "Deep dive into caching strategies",
                "Consider more edge cases",
                "Explore failure scenarios",
            ],
            next_session_recommendations=[
                "Practice database design problems",
                "Focus on distributed systems concepts",
                "Work on API design patterns",
            ],
            generated_at=datetime.now(),
        )

    async def generate_insights(
        self, session_data: Dict[str, Any], conversation_history: List[Dict[str, Any]]
    ) -> ConversationInsights:
        """Mock conversation insights"""
        await self._simulate_processing()

        return ConversationInsights(
            conversation_flow_quality=random.randint(75, 90),
            engagement_level=random.randint(80, 95),
            depth_progression=random.randint(70, 85),
            key_moments=[
                {
                    "timestamp": "00:05:30",
                    "moment_type": "breakthrough",
                    "description": "Candidate identified the key scalability challenge",
                },
                {
                    "timestamp": "00:15:45",
                    "moment_type": "struggle",
                    "description": "Needed guidance on database partitioning",
                },
                {
                    "timestamp": "00:25:20",
                    "moment_type": "insight",
                    "description": "Made excellent connection between caching and consistency",
                },
            ],
            communication_patterns={
                "clarity": "high",
                "structure": "good",
                "detail_level": "appropriate",
            },
            learning_indicators=[
                "Built upon previous concepts well",
                "Asked clarifying questions",
                "Showed curiosity about trade-offs",
            ],
        )


# Global mock AI service instance
mock_ai_service = MockAIService()


async def get_mock_ai_service() -> MockAIService:
    """Get the mock AI service instance"""
    return mock_ai_service
