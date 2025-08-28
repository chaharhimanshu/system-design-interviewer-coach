"""
Feedback Provider Agent
Advanced StateGraph-based agent for generating comprehensive feedback with architecture analysis
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph, END

from app.domain.entities.session import DifficultyLevel
from app.agents.models.output_schemas import FeedbackResponse
from app.infrastructure.config import settings
from app.shared.logging import get_logger

logger = get_logger(__name__)


class FeedbackProviderAgent:
    """
    Advanced StateGraph-based agent for comprehensive feedback generation

    Multi-step workflow:
    1. Analyze Answer - Extract components and patterns from user's response
    2. Generate Performance Report - Create detailed assessment across multiple dimensions
    3. Generate Architecture Comparison - Compare user approach vs organizational standards
    4. Synthesize Feedback - Combine all components into actionable comprehensive feedback

    Capabilities:
    - Multi-dimensional performance analysis
    - Visual architecture comparisons (ASCII diagrams)
    - Organizational standards compliance checking
    - Personalized learning recommendations
    - Comprehensive feedback synthesis
    """

    def __init__(self):
        # Initialize OpenAI model
        self.llm = ChatOpenAI(
            model=settings.openai.model,
            temperature=settings.openai.feedback_temperature,
            api_key=settings.openai.api_key,
            max_tokens=settings.openai.max_tokens,
        )

        # Create output parser for structured feedback
        self.feedback_parser = PydanticOutputParser(pydantic_object=FeedbackResponse)

        # Create the comprehensive feedback workflow
        self.workflow = self._create_feedback_workflow()

        # Organizational standards for comparison
        self.org_standards = self._load_organizational_standards()

        logger.info("FeedbackProviderAgent initialized with StateGraph workflow")

    def _create_feedback_workflow(self) -> StateGraph:
        """Create the StateGraph workflow for comprehensive feedback generation"""

        def feedback_state(state: Dict[str, Any]) -> Dict[str, Any]:
            """Define the state structure for feedback workflow"""
            return {
                "evaluation_data": state.get("evaluation_data", {}),
                "user_answer": state.get("user_answer", ""),
                "question": state.get("question", ""),
                "topic": state.get("topic", ""),
                "difficulty": state.get("difficulty", "intermediate"),
                "context": state.get("context", {}),
                "org_standards": state.get("org_standards", {}),
                # Workflow outputs
                "answer_analysis": state.get("answer_analysis"),
                "performance_report": state.get("performance_report"),
                "architecture_comparison": state.get("architecture_comparison"),
                "final_feedback": state.get("final_feedback"),
                "step": state.get("step", "start"),
            }

        def analyze_answer(state: Dict[str, Any]) -> Dict[str, Any]:
            """Step 1: Comprehensive answer analysis"""
            logger.info(f"Analyzing user answer for topic: {state['topic']}")

            try:
                analysis_prompt = f"""
                Perform comprehensive analysis of this system design answer:
                
                **Question:** {state['question']}
                **Topic:** {state['topic']}
                **User's Answer:** {state['user_answer']}
                **Difficulty Level:** {state['difficulty']}
                **Evaluation Data:** {json.dumps(state['evaluation_data'], indent=2)}
                
                Extract and analyze:
                1. **Architecture Components**: What system components did they identify?
                2. **Design Patterns**: What patterns or approaches did they use?
                3. **Technology Choices**: What technologies or tools did they mention?
                4. **Scalability Considerations**: How did they address scaling?
                5. **Trade-off Discussions**: What trade-offs did they consider?
                6. **Missing Elements**: What critical aspects were not addressed?
                7. **Strengths in Approach**: What did they do particularly well?
                8. **Problem-Solving Method**: How did they approach the problem?
                
                Provide detailed analysis for each aspect with specific examples from their answer.
                Return as structured JSON with clear categorization.
                """

                response = self.llm.invoke([HumanMessage(content=analysis_prompt)])
                answer_analysis = self._parse_json_response(
                    response.content, "answer_analysis"
                )

                state["answer_analysis"] = answer_analysis
                state["step"] = "analysis_complete"

                logger.info("Answer analysis completed successfully")

            except Exception as e:
                logger.error(f"Error in answer analysis: {str(e)}")
                state["answer_analysis"] = {
                    "error": "Analysis failed",
                    "details": str(e),
                }
                state["step"] = "analysis_error"

            return state

        def generate_performance_report(state: Dict[str, Any]) -> Dict[str, Any]:
            """Step 2: Generate detailed performance report"""
            logger.info("Generating comprehensive performance report")

            try:
                report_prompt = f"""
                Generate a comprehensive performance report based on the analysis:
                
                **Answer Analysis:** {json.dumps(state['answer_analysis'], indent=2)}
                **Evaluation Scores:** {json.dumps(state['evaluation_data'], indent=2)}
                **Topic:** {state['topic']}
                **Difficulty:** {state['difficulty']}
                
                Create detailed performance assessment:
                
                1. **Technical Understanding** (0-10):
                   - Accuracy of technical concepts
                   - Depth of system design knowledge
                   - Understanding of underlying principles
                
                2. **Problem-Solving Approach** (0-10):
                   - Systematic thinking process
                   - Breaking down complex problems
                   - Logical progression through solution
                
                3. **Communication Skills** (0-10):
                   - Clarity of explanations
                   - Structure and organization
                   - Use of appropriate terminology
                
                4. **Architecture Design** (0-10):
                   - Component identification and relationships
                   - Scalability considerations
                   - Design pattern application
                
                5. **Trade-off Analysis** (0-10):
                   - Recognition of design trade-offs
                   - Evaluation of alternatives
                   - Justification of design decisions
                
                For each dimension, provide:
                - Numerical score with justification
                - Specific examples from their answer
                - Areas of strength
                - Areas needing improvement
                - Actionable recommendations
                
                Include overall performance summary and key insights.
                Return as structured JSON.
                """

                response = self.llm.invoke([HumanMessage(content=report_prompt)])
                performance_report = self._parse_json_response(
                    response.content, "performance_report"
                )

                state["performance_report"] = performance_report
                state["step"] = "report_complete"

                logger.info("Performance report generated successfully")

            except Exception as e:
                logger.error(f"Error generating performance report: {str(e)}")
                state["performance_report"] = {
                    "error": "Report generation failed",
                    "details": str(e),
                }
                state["step"] = "report_error"

            return state

        def generate_architecture_comparison(state: Dict[str, Any]) -> Dict[str, Any]:
            """Step 3: Generate expected architecture vs user's approach"""
            logger.info(
                "Generating architecture comparison with organizational standards"
            )

            try:
                comparison_prompt = f"""
                Generate comprehensive architecture comparison:
                
                **User's Approach:** {json.dumps(state['answer_analysis'], indent=2)}
                **Topic:** {state['topic']}
                **Organizational Standards:** {json.dumps(state['org_standards'], indent=2)}
                **Difficulty Level:** {state['difficulty']}
                
                Create detailed comparison:
                
                1. **Expected Architecture (Based on Org Standards):**
                   - High-level system design
                   - Key components and responsibilities
                   - Data flow and communication patterns
                   - Technology stack recommendations
                   - Scalability patterns
                   - Security considerations
                   - Monitoring and observability
                
                2. **User's Proposed Architecture:**
                   - What components did they identify?
                   - What patterns did they use?
                   - How did they structure the solution?
                   - What technologies did they choose?
                
                3. **ASCII Architecture Diagrams:**
                   - Create text-based diagram of expected solution
                   - Create text-based diagram of user's approach
                   - Highlight differences visually
                
                4. **Gap Analysis:**
                   - Missing critical components
                   - Suboptimal design choices
                   - Architectural anti-patterns
                   - Scalability limitations
                   - Security gaps
                
                5. **Improvement Recommendations:**
                   - Specific architectural improvements
                   - Better design patterns to consider
                   - Technology alternatives
                   - Scalability enhancements
                
                6. **Compliance Score:**
                   - How well does their approach align with org standards? (0-100%)
                   - Specific compliance strengths and gaps
                
                Return as structured JSON with visual elements.
                """

                response = self.llm.invoke([HumanMessage(content=comparison_prompt)])
                architecture_comparison = self._parse_json_response(
                    response.content, "architecture_comparison"
                )

                state["architecture_comparison"] = architecture_comparison
                state["step"] = "architecture_complete"

                logger.info("Architecture comparison generated successfully")

            except Exception as e:
                logger.error(f"Error generating architecture comparison: {str(e)}")
                state["architecture_comparison"] = {
                    "error": "Architecture comparison failed",
                    "details": str(e),
                }
                state["step"] = "architecture_error"

            return state

        def synthesize_feedback(state: Dict[str, Any]) -> Dict[str, Any]:
            """Step 4: Combine all components into comprehensive final feedback"""
            logger.info("Synthesizing comprehensive feedback")

            try:
                synthesis_prompt = f"""
                Synthesize all analysis into comprehensive, actionable feedback:
                
                **Components to Synthesize:**
                - Answer Analysis: {json.dumps(state['answer_analysis'], indent=2)}
                - Performance Report: {json.dumps(state['performance_report'], indent=2)}
                - Architecture Comparison: {json.dumps(state['architecture_comparison'], indent=2)}
                
                **Context:**
                - Topic: {state['topic']}
                - Difficulty: {state['difficulty']}
                - Conversation Context: {json.dumps(state['context'], indent=2)}
                
                Create comprehensive feedback with:
                
                1. **Executive Summary:**
                   - Overall performance assessment (2-3 sentences)
                   - Key strengths and accomplishments
                   - Primary areas for improvement
                   - Overall recommendation/grade
                
                2. **Detailed Performance Analysis:**
                   - Technical knowledge demonstration
                   - Problem-solving effectiveness
                   - Communication clarity and structure
                   - Architectural thinking quality
                   - Trade-off analysis capability
                
                3. **Architecture Insights:**
                   - Comparison summary with visual elements
                   - Critical gaps in their design
                   - Organizational standard alignment
                   - Specific architectural improvements
                
                4. **Learning Roadmap:**
                   - Immediate focus areas (next 1-2 weeks)
                   - Medium-term learning goals (1-3 months)
                   - Long-term development areas (3+ months)
                   - Specific resources and practice suggestions
                
                5. **Next Interview Preparation:**
                   - What to practice before next session
                   - Specific topics to study
                   - Mock interview recommendations
                   - Confidence building activities
                
                6. **Encouragement & Motivation:**
                   - Positive reinforcement message
                   - Growth mindset encouragement
                   - Recognition of effort and progress
                   - Inspiration for continued learning
                
                Make feedback constructive, specific, actionable, and encouraging.
                Return as structured JSON matching FeedbackResponse schema.
                
                {self.feedback_parser.get_format_instructions()}
                """

                response = self.llm.invoke([HumanMessage(content=synthesis_prompt)])

                # Parse structured feedback response
                try:
                    final_feedback = self.feedback_parser.parse(response.content)
                    final_feedback.generated_at = datetime.now()
                except Exception as parse_error:
                    logger.error(f"Error parsing structured feedback: {parse_error}")
                    # Fall back to basic JSON parsing
                    final_feedback = self._parse_json_response(
                        response.content, "final_feedback"
                    )

                state["final_feedback"] = final_feedback
                state["step"] = "complete"

                logger.info("Comprehensive feedback synthesis completed successfully")

            except Exception as e:
                logger.error(f"Error synthesizing feedback: {str(e)}")
                state["final_feedback"] = self._create_fallback_feedback()
                state["step"] = "synthesis_error"

            return state

        # Create the workflow graph
        workflow = StateGraph(feedback_state)

        # Add nodes for each step
        workflow.add_node("analyze", analyze_answer)
        workflow.add_node("report", generate_performance_report)
        workflow.add_node("architecture", generate_architecture_comparison)
        workflow.add_node("synthesize", synthesize_feedback)

        # Define workflow progression
        workflow.add_edge("analyze", "report")
        workflow.add_edge("report", "architecture")
        workflow.add_edge("architecture", "synthesize")
        workflow.add_edge("synthesize", END)

        # Set entry point
        workflow.set_entry_point("analyze")

        return workflow.compile()

    async def generate_comprehensive_feedback(
        self,
        evaluation_data: Dict[str, Any],
        user_answer: str,
        question: str,
        topic: str,
        difficulty: DifficultyLevel,
        context: Dict[str, Any],
    ) -> FeedbackResponse:
        """
        Generate comprehensive feedback using StateGraph workflow

        Args:
            evaluation_data: Answer evaluation results
            user_answer: The user's complete answer
            question: The original question asked
            topic: Interview topic
            difficulty: Difficulty level
            context: Interview context and history

        Returns:
            Comprehensive structured feedback response
        """
        logger.info(f"Starting comprehensive feedback generation for topic: {topic}")

        # Prepare initial state for workflow
        initial_state = {
            "evaluation_data": evaluation_data,
            "user_answer": user_answer,
            "question": question,
            "topic": topic,
            "difficulty": difficulty.value,
            "context": context,
            "org_standards": self.org_standards.get(
                topic, self.org_standards.get("general", {})
            ),
            "step": "start",
        }

        # Run the comprehensive feedback workflow
        result = await self.workflow.ainvoke(initial_state)

        feedback_response = result["final_feedback"]

        logger.info(f"Comprehensive feedback generated successfully")

        return feedback_response

    async def generate_quick_feedback(
        self,
        evaluation: Dict[str, Any],
        topic: str,
        difficulty: DifficultyLevel,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate quick contextual feedback for immediate response

        Args:
            evaluation: Answer evaluation results
            topic: Interview topic
            difficulty: Difficulty level
            context: Interview context

        Returns:
            Quick feedback dict with immediate insights
        """
        logger.info("Generating quick contextual feedback")

        # Determine appropriate feedback style
        feedback_style = self._determine_feedback_style(evaluation, context)

        try:
            quick_prompt = f"""
            Generate immediate, contextual feedback for this system design answer evaluation:
            
            **Evaluation Results:** {json.dumps(evaluation, indent=2)}
            **Topic:** {topic}
            **Difficulty:** {difficulty.value}
            **Style:** {feedback_style}
            **Context:** {json.dumps(context, indent=2)}
            
            Provide concise but meaningful feedback with:
            1. **Immediate Recognition**: What they did well right now
            2. **Quick Insight**: One key insight or correction
            3. **Gentle Guidance**: Where to focus next
            4. **Encouragement**: Motivational message
            
            Keep response conversational and supportive.
            Return as JSON with: recognition, insight, guidance, encouragement
            """

            response = self.llm.invoke([HumanMessage(content=quick_prompt)])
            feedback_result = self._parse_json_response(
                response.content, "quick_feedback"
            )

            # Add metadata
            feedback_result["style_used"] = feedback_style
            feedback_result["generated_at"] = datetime.now().isoformat()

            return feedback_result

        except Exception as e:
            logger.error(f"Error generating quick feedback: {str(e)}")
            return {
                "recognition": "Thank you for your thoughtful response.",
                "insight": "Let's explore this topic further together.",
                "guidance": "Think about the key components and their relationships.",
                "encouragement": "You're making good progress. Keep thinking systematically!",
                "error": str(e),
            }

    async def generate_encouragement(
        self,
        current_struggle: str,
        difficulty: DifficultyLevel,
        progress_so_far: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate encouraging message when candidate is struggling
        """
        logger.info("Generating encouragement for struggling candidate")

        try:
            encouragement_prompt = f"""
            Generate encouraging message for a candidate struggling with: {current_struggle}
            
            Context:
            - Difficulty Level: {difficulty.value}
            - Progress So Far: {json.dumps(progress_so_far, indent=2)}
            
            Create supportive message that:
            1. Acknowledges the challenge without making them feel worse
            2. Reminds them of their progress and strengths
            3. Provides gentle, specific guidance to move forward
            4. Builds confidence while maintaining realistic expectations
            5. Uses growth mindset language
            
            Return JSON with: message, guidance, reminder, reframe, next_step
            """

            response = self.llm.invoke([HumanMessage(content=encouragement_prompt)])
            return self._parse_json_response(response.content, "encouragement")

        except Exception as e:
            logger.error(f"Error generating encouragement: {str(e)}")
            return {
                "message": "System design can be challenging, but you're learning and growing with each question.",
                "guidance": "Try breaking the problem down into smaller, manageable components.",
                "reminder": "You've already shown good thinking in previous responses.",
                "reframe": "This challenge is an opportunity to deepen your understanding.",
                "next_step": "Let's focus on one aspect at a time and build from there.",
            }

    def _load_organizational_standards(self) -> Dict[str, Any]:
        """Load organizational standards for architecture comparison"""
        return {
            "general": {
                "preferred_patterns": [
                    "Microservices for scalability",
                    "Event-driven architecture for decoupling",
                    "CQRS for read/write separation",
                    "Circuit breaker for resilience",
                    "API Gateway for external access",
                ],
                "technology_stack": {
                    "cloud": "AWS/Azure/GCP",
                    "containers": "Docker + Kubernetes",
                    "databases": ["PostgreSQL", "MongoDB", "Redis"],
                    "messaging": ["Apache Kafka", "RabbitMQ", "AWS SQS"],
                    "monitoring": ["Prometheus", "Grafana", "ELK Stack"],
                    "api": "REST + GraphQL",
                },
                "security_requirements": [
                    "Authentication and authorization at all layers",
                    "Data encryption in transit and at rest",
                    "API rate limiting and throttling",
                    "Input validation and sanitization",
                    "Audit logging for all operations",
                ],
                "scalability_patterns": [
                    "Horizontal scaling over vertical",
                    "Load balancing across multiple instances",
                    "Caching strategies (Redis/Memcached)",
                    "Database sharding and replication",
                    "CDN for static content delivery",
                ],
                "reliability_requirements": [
                    "99.9% uptime SLA minimum",
                    "Disaster recovery planning",
                    "Health checks and monitoring",
                    "Graceful degradation strategies",
                    "Automated failover mechanisms",
                ],
            },
            "chat_application": {
                "core_components": [
                    "User Service",
                    "Message Service",
                    "Notification Service",
                    "Real-time Service",
                ],
                "real_time": "WebSockets or Server-Sent Events",
                "message_storage": "NoSQL (MongoDB) + Message Queue",
                "scaling_focus": "Connection management and message throughput",
            },
            "url_shortener": {
                "core_components": [
                    "URL Service",
                    "Analytics Service",
                    "Cache Layer",
                    "Database Layer",
                ],
                "database_choice": "NoSQL for URL mappings + SQL for analytics",
                "caching_strategy": "Multi-layer caching (Redis + CDN)",
                "scaling_focus": "Read-heavy workload optimization",
            },
            "social_media_feed": {
                "core_components": [
                    "User Service",
                    "Post Service",
                    "Feed Generation Service",
                    "Notification Service",
                ],
                "architecture_pattern": "Event-driven with message queues",
                "feed_strategy": "Push vs Pull vs Hybrid models",
                "scaling_focus": "Feed generation and real-time updates",
            },
        }

    def _determine_feedback_style(
        self, evaluation: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        """Determine appropriate feedback style based on evaluation and context"""

        avg_score = self._calculate_average_score(evaluation)
        question_count = context.get("question_count", 0)
        confidence = evaluation.get("confidence_level", 0.5)

        # Determine style based on performance, confidence, and stage
        if avg_score >= 8 and confidence >= 0.8:
            return "challenging"  # Push high performers further
        elif avg_score >= 6 and confidence >= 0.6:
            return "constructive"  # Balanced feedback
        elif question_count <= 2:
            return "encouraging"  # Be encouraging early on
        else:
            return "supportive"  # Build confidence for struggling candidates

    def _calculate_average_score(self, evaluation: Dict[str, Any]) -> float:
        """Calculate average score from evaluation metrics"""
        scores = []

        # Try different possible score field structures
        if "scores" in evaluation and hasattr(evaluation["scores"], "__dict__"):
            score_obj = evaluation["scores"]
            for attr_name in [
                "clarity",
                "technical_depth",
                "scalability_awareness",
                "trade_offs_understanding",
            ]:
                if hasattr(score_obj, attr_name):
                    scores.append(getattr(score_obj, attr_name))
        elif "scores" in evaluation and isinstance(evaluation["scores"], dict):
            score_dict = evaluation["scores"]
            for field in [
                "clarity",
                "technical_depth",
                "scalability_awareness",
                "trade_offs_understanding",
            ]:
                if field in score_dict:
                    scores.append(score_dict[field])
        else:
            # Try direct field access
            for field in [
                "clarity_score",
                "technical_depth",
                "scalability_awareness",
                "trade_offs_understanding",
            ]:
                if field in evaluation and evaluation[field] is not None:
                    scores.append(evaluation[field])

        return sum(scores) / len(scores) if scores else 5.0

    def _parse_json_response(
        self, response: str, context: str = "response"
    ) -> Dict[str, Any]:
        """Parse JSON response from LLM with error handling"""
        try:
            # Extract JSON from response if it's wrapped in markdown
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
            logger.error(f"Failed to parse JSON response for {context}: {str(e)}")
            logger.error(f"Response content: {response[:500]}...")

            # Return context-appropriate fallback
            if context == "answer_analysis":
                return {
                    "architecture_components": ["Analysis unavailable"],
                    "design_patterns": ["Could not determine"],
                    "strengths": ["Response provided"],
                    "areas_for_improvement": ["Analysis parsing failed"],
                }
            elif context == "performance_report":
                return {
                    "technical_understanding": 5.0,
                    "problem_solving_approach": 5.0,
                    "communication_skills": 5.0,
                    "overall_summary": "Performance assessment unavailable due to parsing error",
                }
            else:
                return {
                    "message": "Analysis temporarily unavailable",
                    "error": f"JSON parsing failed for {context}",
                    "timestamp": datetime.now().isoformat(),
                }

    def _create_fallback_feedback(self) -> Dict[str, Any]:
        """Create fallback feedback when synthesis fails"""
        logger.warning("Creating fallback feedback due to synthesis error")

        return {
            "executive_summary": "Thank you for your thoughtful response to this system design question.",
            "performance_analysis": {
                "technical_knowledge": "Demonstrated effort in approaching the problem",
                "problem_solving": "Attempted to break down the requirements",
                "communication": "Provided structured response",
                "overall_assessment": "Feedback generation encountered technical difficulties",
            },
            "learning_roadmap": {
                "immediate_focus": ["Review system design fundamentals"],
                "medium_term_goals": ["Practice with more system design problems"],
                "resources": [
                    "System Design Interview books",
                    "Online practice platforms",
                ],
            },
            "encouragement": "Keep practicing system design problems. Each attempt helps build your skills and confidence.",
            "error_note": "Comprehensive feedback temporarily unavailable",
            "generated_at": datetime.now().isoformat(),
        }
