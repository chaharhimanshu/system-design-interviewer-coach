"""
Answer Evaluator Agent
OpenAI-powered React agent for evaluating system design interview answers with multiple analytical tools
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from app.domain.entities.session import DifficultyLevel
from app.agents.models.output_schemas import (
    AnswerEvaluation,
    ConversationInsights,
    EvaluationScores,
    AnswerAnalysis,
    NextSteps,
)
from app.agents.prompts.evaluation_prompts import (
    EVALUATION_SYSTEM_PROMPTS,
    EVALUATION_PROMPTS,
    TOPIC_EVALUATION_GUIDELINES,
    SCORING_RUBRICS,
)
from app.infrastructure.config import settings
from app.shared.logging import get_logger

logger = get_logger(__name__)


class AnswerEvaluatorAgent:
    """
    OpenAI React Agent specialized in evaluating system design interview answers
    Uses multiple analytical tools for comprehensive evaluation with structured outputs
    """

    def __init__(self):
        # Initialize OpenAI model with structured output support
        self.llm = ChatOpenAI(
            model=settings.openai.model,
            temperature=settings.openai.evaluation_temperature,
            api_key=settings.openai.api_key,
            max_tokens=settings.openai.max_tokens,
        )

        # Create output parsers for different response types
        self.evaluation_parser = PydanticOutputParser(pydantic_object=AnswerEvaluation)
        self.insights_parser = PydanticOutputParser(
            pydantic_object=ConversationInsights
        )

        # Store current evaluation context for tools
        self.current_context = {}

        # Create the React agent with analytical tools
        self.agent = self._create_react_agent()

        logger.info(
            "AnswerEvaluatorAgent initialized with React agent and analytical tools"
        )

    def _create_technical_analysis_tool(self):
        """Tool for analyzing technical accuracy and correctness"""

        def technical_analysis(answer: str, topic: str, difficulty: str) -> str:
            """
            Analyze the technical accuracy of the answer.

            Args:
                answer: The user's answer to analyze
                topic: The topic being discussed
                difficulty: The difficulty level (beginner, intermediate, advanced)

            Returns:
                Technical analysis with accuracy assessment and corrections
            """
            try:
                prompt = f"""
                Analyze the technical accuracy of this system design answer:
                
                Topic: {topic}
                Difficulty: {difficulty}
                Answer: {answer}
                
                Evaluate:
                1. Technical correctness of statements
                2. Proper use of terminology
                3. Adherence to industry best practices
                4. Common misconceptions or errors
                5. Missing critical technical details
                
                Provide specific technical feedback with corrections where needed.
                Score technical accuracy from 1-10.
                """

                response = self.llm.invoke([HumanMessage(content=prompt)])
                return response.content

            except Exception as e:
                logger.error(f"Error in technical analysis: {e}")
                return f"Technical analysis unavailable: {str(e)}"

        return technical_analysis

    def _create_completeness_assessment_tool(self):
        """Tool for assessing answer completeness and coverage"""

        def completeness_assessment(
            answer: str, topic: str, expected_concepts: List[str]
        ) -> str:
            """
            Assess how complete and comprehensive the answer is.

            Args:
                answer: The user's answer to assess
                topic: The topic being discussed
                expected_concepts: List of concepts that should be covered

            Returns:
                Completeness analysis with coverage assessment
            """
            try:
                concepts_str = (
                    ", ".join(expected_concepts)
                    if expected_concepts
                    else "Standard system design concepts"
                )

                prompt = f"""
                Assess the completeness of this system design answer:
                
                Topic: {topic}
                Expected concepts: {concepts_str}
                Answer: {answer}
                
                Evaluate:
                1. Coverage of key concepts and components
                2. Depth of discussion for each area
                3. Missing important topics or considerations
                4. Breadth vs. depth balance
                5. Completeness relative to topic complexity
                
                Identify specific gaps and score completeness from 1-10.
                """

                response = self.llm.invoke([HumanMessage(content=prompt)])
                return response.content

            except Exception as e:
                logger.error(f"Error in completeness assessment: {e}")
                return f"Completeness assessment unavailable: {str(e)}"

        return completeness_assessment

    def _create_clarity_evaluation_tool(self):
        """Tool for evaluating communication clarity and structure"""

        def clarity_evaluation(answer: str, difficulty: str) -> str:
            """
            Evaluate the clarity and communication quality of the answer.

            Args:
                answer: The user's answer to evaluate
                difficulty: The difficulty level for appropriate expectations

            Returns:
                Clarity analysis with communication feedback
            """
            try:
                prompt = f"""
                Evaluate the clarity and communication quality of this answer:
                
                Difficulty Level: {difficulty}
                Answer: {answer}
                
                Assess:
                1. Logical flow and structure
                2. Clear explanation of concepts
                3. Use of appropriate examples or analogies
                4. Conciseness vs. thoroughness balance
                5. Technical communication skills
                6. Ability to explain complex concepts simply
                
                Provide specific feedback on communication effectiveness.
                Score clarity from 1-10.
                """

                response = self.llm.invoke([HumanMessage(content=prompt)])
                return response.content

            except Exception as e:
                logger.error(f"Error in clarity evaluation: {e}")
                return f"Clarity evaluation unavailable: {str(e)}"

        return clarity_evaluation

    def _create_depth_analysis_tool(self):
        """Tool for analyzing technical depth and sophistication"""

        def depth_analysis(answer: str, topic: str, difficulty: str) -> str:
            """
            Analyze the technical depth and sophistication of the answer.

            Args:
                answer: The user's answer to analyze
                topic: The topic being discussed
                difficulty: Expected difficulty level

            Returns:
                Depth analysis with sophistication assessment
            """
            try:
                prompt = f"""
                Analyze the technical depth and sophistication of this answer:
                
                Topic: {topic}
                Expected Difficulty: {difficulty}
                Answer: {answer}
                
                Evaluate:
                1. Level of technical detail provided
                2. Understanding of underlying principles
                3. Sophistication of proposed solutions
                4. Awareness of advanced concepts
                5. Appropriate depth for difficulty level
                6. Evidence of deep system design knowledge
                
                Compare depth against expectations for {difficulty} level.
                Score technical depth from 1-10.
                """

                response = self.llm.invoke([HumanMessage(content=prompt)])
                return response.content

            except Exception as e:
                logger.error(f"Error in depth analysis: {e}")
                return f"Depth analysis unavailable: {str(e)}"

        return depth_analysis

    def _create_scalability_check_tool(self):
        """Tool for checking scalability awareness and considerations"""

        def scalability_check(answer: str, topic: str) -> str:
            """
            Check the scalability awareness and considerations in the answer.

            Args:
                answer: The user's answer to check
                topic: The topic being discussed

            Returns:
                Scalability analysis with recommendations
            """
            try:
                prompt = f"""
                Analyze scalability awareness in this system design answer:
                
                Topic: {topic}
                Answer: {answer}
                
                Evaluate:
                1. Recognition of scalability challenges
                2. Proposed scaling strategies (horizontal/vertical)
                3. Understanding of bottlenecks and solutions
                4. Load distribution and caching strategies
                5. Database scaling considerations
                6. Infrastructure scaling awareness
                
                Identify missed scalability opportunities.
                Score scalability awareness from 1-10.
                """

                response = self.llm.invoke([HumanMessage(content=prompt)])
                return response.content

            except Exception as e:
                logger.error(f"Error in scalability check: {e}")
                return f"Scalability check unavailable: {str(e)}"

        return scalability_check

    def _create_best_practices_tool(self):
        """Tool for verifying adherence to industry best practices"""

        def best_practices_check(answer: str, topic: str) -> str:
            """
            Check adherence to industry best practices and standards.

            Args:
                answer: The user's answer to verify
                topic: The topic area for relevant practices

            Returns:
                Best practices analysis with recommendations
            """
            try:
                prompt = f"""
                Verify adherence to industry best practices in this answer:
                
                Topic: {topic}
                Answer: {answer}
                
                Check for:
                1. Industry-standard design patterns
                2. Security best practices and considerations
                3. Performance optimization techniques
                4. Reliability and fault tolerance patterns
                5. Monitoring and observability practices
                6. Data consistency and integrity approaches
                
                Identify deviations from best practices and suggest improvements.
                Score best practices adherence from 1-10.
                """

                response = self.llm.invoke([HumanMessage(content=prompt)])
                return response.content

            except Exception as e:
                logger.error(f"Error in best practices check: {e}")
                return f"Best practices check unavailable: {str(e)}"

        return best_practices_check

    def _create_gap_identification_tool(self):
        """Tool for identifying knowledge gaps and missing concepts"""

        def gap_identification(answer: str, topic: str, difficulty: str) -> str:
            """
            Identify knowledge gaps and missing concepts in the answer.

            Args:
                answer: The user's answer to analyze
                topic: The topic being discussed
                difficulty: The expected difficulty level

            Returns:
                Gap analysis with specific learning recommendations
            """
            try:
                prompt = f"""
                Identify knowledge gaps and missing concepts in this answer:
                
                Topic: {topic}
                Difficulty Level: {difficulty}
                Answer: {answer}
                
                Analyze:
                1. Critical concepts not mentioned or misunderstood
                2. Important system design principles overlooked
                3. Common pitfalls not addressed
                4. Advanced concepts missing for difficulty level
                5. Fundamental gaps in understanding
                6. Areas needing immediate attention
                
                Prioritize gaps by importance and provide specific learning recommendations.
                """

                response = self.llm.invoke([HumanMessage(content=prompt)])
                return response.content

            except Exception as e:
                logger.error(f"Error in gap identification: {e}")
                return f"Gap identification unavailable: {str(e)}"

        return gap_identification

    def _create_react_agent(self):
        """Create the React agent with all analytical tools"""
        tools = [
            self._create_technical_analysis_tool(),
            self._create_completeness_assessment_tool(),
            self._create_clarity_evaluation_tool(),
            self._create_depth_analysis_tool(),
            self._create_scalability_check_tool(),
            self._create_best_practices_tool(),
            self._create_gap_identification_tool(),
        ]

        system_prompt = """
        You are an expert system design interview evaluator with deep technical knowledge across all areas of distributed systems, scalability, and software architecture.
        
        Your role is to provide comprehensive, fair, and actionable evaluations of system design interview answers.
        
        Evaluation Process:
        1. Use technical_analysis tool to verify correctness and identify technical errors
        2. Use completeness_assessment tool to check coverage of expected concepts
        3. Use clarity_evaluation tool to assess communication effectiveness
        4. Use depth_analysis tool to gauge technical sophistication level
        5. Use scalability_check tool to verify scaling awareness and strategies
        6. Use best_practices_check tool to compare against industry standards
        7. Use gap_identification tool to find missing concepts and learning opportunities
        
        Always use ALL tools to provide multi-dimensional analysis. Synthesize findings into:
        - Specific strengths and positive aspects
        - Clear weaknesses and areas for improvement
        - Missing topics that should be addressed
        - Technical errors that need correction
        - Actionable next steps for the candidate
        
        Be constructive, specific, and helpful in your evaluation. Focus on learning and growth.
        Provide scores from 1-10 for each dimension and explain your reasoning.
        """

        return create_react_agent(
            model=self.llm, tools=tools, state_modifier=system_prompt
        )

    async def evaluate_answer(
        self,
        question: str,
        answer: str,
        topic: str,
        difficulty: DifficultyLevel,
        context: Dict[str, Any],
    ) -> AnswerEvaluation:
        """
        Comprehensive evaluation of user's answer using React agent with analytical tools
        """
        logger.info(
            f"Starting answer evaluation for topic: {topic}, difficulty: {difficulty}"
        )

        # Store context for tools to use
        self.current_context = {
            "question": question,
            "topic": topic,
            "difficulty": difficulty.value,
            "context": context,
        }

        try:
            # Create comprehensive evaluation prompt for React agent
            evaluation_prompt = f"""
            Please evaluate this system design interview answer using all your analytical tools:
            
            **Interview Context:**
            - Topic: {topic}
            - Difficulty Level: {difficulty.value}
            - Question: {question}
            
            **User's Answer:**
            {answer}
            
            **Evaluation Requirements:**
            1. Use technical_analysis to verify correctness and identify technical errors
            2. Use completeness_assessment to check coverage (expected concepts for {topic})
            3. Use clarity_evaluation to assess communication effectiveness
            4. Use depth_analysis to gauge technical sophistication for {difficulty.value} level
            5. Use scalability_check to verify scaling awareness and strategies
            6. Use best_practices_check to compare against industry standards
            7. Use gap_identification to find missing concepts and learning opportunities
            
            After using all tools, provide a comprehensive synthesis with:
            - Overall assessment and key insights
            - Specific scores (1-10) for: clarity, technical_depth, scalability_awareness, trade_offs_understanding
            - Detailed strengths and weaknesses
            - Missing topics that should be addressed
            - Technical errors needing correction
            - Specific next steps and areas to explore
            - Confidence level in this evaluation (0.0-1.0)
            
            Be constructive, specific, and actionable in your evaluation.
            """

            # Run the React agent evaluation
            agent_response = await self.agent.ainvoke(
                {"messages": [HumanMessage(content=evaluation_prompt)]}
            )

            # Extract the evaluation from agent response
            agent_output = agent_response.get("messages", [])[-1].content

            # Parse the structured evaluation using the comprehensive response
            evaluation = self._parse_agent_evaluation(
                agent_output, question, answer, topic, difficulty
            )

            logger.info(
                f"Evaluation completed with average score: {evaluation.scores.average_score:.2f}"
            )

            return evaluation

        except Exception as e:
            logger.error(f"Error in answer evaluation: {str(e)}")
            return self._create_fallback_evaluation()

    def _parse_agent_evaluation(
        self,
        agent_output: str,
        question: str,
        answer: str,
        topic: str,
        difficulty: DifficultyLevel,
    ) -> AnswerEvaluation:
        """Parse the agent's comprehensive evaluation into structured format"""
        try:
            # Use a focused prompt to extract structured data from agent evaluation
            parsing_prompt = f"""
            Extract structured evaluation data from this comprehensive evaluation:
            
            {agent_output}
            
            {self.evaluation_parser.get_format_instructions()}
            
            Focus on extracting:
            - Numerical scores for clarity, technical_depth, scalability_awareness, trade_offs_understanding
            - Lists of strengths, weaknesses, missing_topics, technical_errors
            - Next steps information including needs_clarification, needs_deeper_dive, ready_for_next_topic
            - Suggested follow-up and specific areas to explore
            - Confidence level
            
            Ensure all scores are realistic (1-10) and all text fields are meaningful and specific.
            """

            response = self.llm.invoke([HumanMessage(content=parsing_prompt)])
            evaluation = self.evaluation_parser.parse(response.content)

            # Add metadata
            evaluation.evaluation_timestamp = datetime.now()

            return evaluation

        except Exception as e:
            logger.error(f"Error parsing agent evaluation: {str(e)}")
            return self._create_fallback_evaluation()

    async def evaluate_conversation_flow(
        self,
        conversation_history: List[Dict[str, Any]],
        topic: str,
        difficulty: DifficultyLevel,
    ) -> ConversationInsights:
        """
        Evaluate the overall conversation flow and progress using React agent analysis
        """
        logger.info("Evaluating conversation flow with React agent")

        try:
            # Create conversation analysis prompt
            conversation_prompt = f"""
            Analyze this system design interview conversation flow and provide insights:
            
            **Context:**
            - Topic: {topic}
            - Difficulty: {difficulty.value}
            
            **Conversation History:**
            {json.dumps(conversation_history, indent=2)}
            
            **Analysis Required:**
            Please evaluate:
            1. Coverage completeness - what percentage of the topic has been covered?
            2. Progression quality - how well is the conversation flowing?
            3. Candidate growth indicators - signs of learning and improvement
            4. Recommended focus areas - what should be emphasized next
            5. Key achievements - what has the candidate done well?
            6. Remaining critical topics - what essential areas are still needed?
            
            Provide specific, actionable insights for improving the interview experience.
            """

            # Run analysis through React agent
            agent_response = await self.agent.ainvoke(
                {"messages": [HumanMessage(content=conversation_prompt)]}
            )

            agent_output = agent_response.get("messages", [])[-1].content

            # Parse structured insights
            insights = self._parse_conversation_insights(agent_output)

            logger.info(
                f"Conversation flow evaluated - completion: {insights.estimated_completion_percentage}%"
            )

            return insights

        except Exception as e:
            logger.error(f"Error evaluating conversation flow: {str(e)}")
            # Return fallback insights
            return ConversationInsights(
                coverage_completeness=50.0,
                progression_quality=5.0,
                candidate_growth_indicators=["Attempting to engage with questions"],
                recommended_focus_areas=["Continue current discussion"],
                estimated_completion_percentage=50.0,
                key_achievements=["Participated in interview"],
                remaining_critical_topics=["All major topics"],
            )

    def _parse_conversation_insights(self, agent_output: str) -> ConversationInsights:
        """Parse conversation insights from agent analysis"""
        try:
            parsing_prompt = f"""
            Extract structured conversation insights from this analysis:
            
            {agent_output}
            
            {self.insights_parser.get_format_instructions()}
            
            Ensure all numerical values are realistic percentages and scores.
            Provide specific, actionable items in all list fields.
            """

            response = self.llm.invoke([HumanMessage(content=parsing_prompt)])
            insights = self.insights_parser.parse(response.content)

            return insights

        except Exception as e:
            logger.error(f"Error parsing conversation insights: {str(e)}")
            return ConversationInsights(
                coverage_completeness=50.0,
                progression_quality=5.0,
                candidate_growth_indicators=["Analysis unavailable"],
                recommended_focus_areas=["Continue current discussion"],
                estimated_completion_percentage=50.0,
                key_achievements=["Participated in interview"],
                remaining_critical_topics=["Unable to determine"],
            )

    async def evaluate_technical_accuracy(
        self, answer: str, topic_area: str, expected_concepts: List[str]
    ) -> Dict[str, Any]:
        """
        Focused evaluation of technical accuracy using React agent tools
        """
        logger.info(f"Evaluating technical accuracy for area: {topic_area}")

        try:
            accuracy_prompt = f"""
            Use your technical analysis tools to evaluate the accuracy of this answer:
            
            **Topic Area:** {topic_area}
            **Expected Concepts:** {expected_concepts}
            **Answer:** {answer}
            
            Focus specifically on:
            1. Technical correctness and accuracy
            2. Proper terminology usage
            3. Alignment with expected concepts
            4. Identification of misconceptions or errors
            
            Provide detailed technical analysis with specific feedback and corrections.
            """

            # Use React agent for focused technical analysis
            agent_response = await self.agent.ainvoke(
                {"messages": [HumanMessage(content=accuracy_prompt)]}
            )

            technical_analysis = agent_response.get("messages", [])[-1].content

            return {
                "technical_analysis": technical_analysis,
                "evaluated_at": datetime.now().isoformat(),
                "topic_area": topic_area,
                "concepts_evaluated": expected_concepts,
                "analysis_method": "React agent with analytical tools",
            }

        except Exception as e:
            logger.error(f"Error in technical accuracy evaluation: {str(e)}")
            return {
                "technical_analysis": "Technical evaluation unavailable",
                "error": str(e),
                "evaluated_at": datetime.now().isoformat(),
            }

    def _create_fallback_evaluation(self) -> AnswerEvaluation:
        """Create a fallback evaluation when parsing fails"""
        logger.warning("Creating fallback evaluation due to parsing error")

        return AnswerEvaluation(
            scores=EvaluationScores(
                clarity=5.0,
                technical_depth=5.0,
                scalability_awareness=5.0,
                trade_offs_understanding=5.0,
            ),
            analysis=AnswerAnalysis(
                strengths=["Answer provided"],
                weaknesses=["Evaluation parsing failed - manual review needed"],
                missing_topics=["Unknown due to parsing error"],
                technical_errors=["Could not analyze due to technical issue"],
            ),
            next_steps=NextSteps(
                needs_clarification=True,
                needs_deeper_dive=False,
                ready_for_next_topic=False,
                suggested_follow_up="clarification",
                specific_areas_to_explore=["Please rephrase your answer"],
            ),
            confidence_level=0.3,
        )
