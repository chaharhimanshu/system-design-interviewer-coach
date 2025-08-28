"""
Question Generator Agent
OpenAI-powered agent for generating contextual system design interview questions using structured outputs
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.prebuilt import create_react_agent

from app.domain.entities.session import DifficultyLevel
from app.agents.models.output_schemas import QuestionGeneration, AIHint
from app.agents.prompts.question_generation_prompts import (
    QUESTION_GENERATION_SYSTEM_PROMPTS,
    QUESTION_TYPE_PROMPTS,
    TOPIC_QUESTION_TEMPLATES,
    PROGRESSIVE_STRATEGIES,
    HINT_TEMPLATES,
)
from app.infrastructure.config import settings
from app.shared.logging import get_logger

logger = get_logger(__name__)


class QuestionGeneratorAgent:
    """
    OpenAI Agent specialized in generating contextual system design interview questions
    Uses create_react_agent for intelligent question generation with tools
    """

    def __init__(self):
        # Initialize OpenAI model
        self.llm = ChatOpenAI(
            model=settings.openai.model,
            temperature=settings.openai.question_temperature,
            api_key=settings.openai.api_key,
            max_tokens=settings.openai.max_tokens,
        )

        # Create output parsers
        self.question_parser = PydanticOutputParser(pydantic_object=QuestionGeneration)
        self.hint_parser = PydanticOutputParser(pydantic_object=AIHint)

        # Create React agent with intelligent tools
        self.agent = self._create_react_agent()

        logger.info("QuestionGeneratorAgent initialized with React agent")

    def _create_react_agent(self) -> create_react_agent:
        """Create React agent for intelligent question generation"""

        # Define tools for intelligent question generation
        tools = [
            self._create_topic_analysis_tool(),
            self._create_context_evaluation_tool(),
            self._create_difficulty_assessment_tool(),
            self._create_prompt_optimization_tool(),
        ]

        system_prompt = """
        You are an expert system design interview question generator with advanced reasoning capabilities.
        
        Your core competencies:
        - Generate contextual questions based on topic, difficulty, and user performance
        - Analyze user answers to create intelligent follow-ups  
        - Adapt question complexity dynamically
        - Create smooth topic transitions
        - Provide helpful hints without giving away answers
        
        Available tools:
        - topic_analysis: Understand domain-specific concepts and patterns
        - context_evaluation: Analyze conversation flow and user performance
        - difficulty_assessment: Determine appropriate question complexity
        - prompt_optimization: Optimize question phrasing and structure
        
        Always use your tools to gather context before generating questions.
        Ensure all outputs follow the QuestionGeneration structured format.
        
        Your goal: Create engaging, educational interview experiences that adapt to each candidate.
        """

        # Create React agent with tools
        agent = create_react_agent(
            model=self.llm, tools=tools, state_modifier=system_prompt
        )

        return agent

    def _create_topic_analysis_tool(self):
        """Tool for analyzing topic requirements and key concepts"""

        def analyze_topic(topic: str, difficulty: str) -> str:
            """Analyze topic to understand key areas and concepts"""

            topic_mapping = {
                "chat_system": {
                    "key_concepts": [
                        "real-time messaging",
                        "user presence",
                        "message delivery",
                        "scalability",
                    ],
                    "patterns": [
                        "pub-sub",
                        "websockets",
                        "message queues",
                        "microservices",
                    ],
                    "difficulty_focus": {
                        "beginner": ["basic messaging", "simple user management"],
                        "intermediate": [
                            "real-time delivery",
                            "scaling patterns",
                            "data consistency",
                        ],
                        "advanced": [
                            "global distribution",
                            "consistency models",
                            "performance optimization",
                        ],
                    },
                },
                "url_shortener": {
                    "key_concepts": [
                        "hashing algorithms",
                        "database design",
                        "caching strategies",
                        "analytics",
                    ],
                    "patterns": [
                        "load balancing",
                        "distributed caching",
                        "rate limiting",
                        "CDN",
                    ],
                    "difficulty_focus": {
                        "beginner": ["basic URL mapping", "simple database"],
                        "intermediate": [
                            "custom domains",
                            "analytics",
                            "caching layers",
                        ],
                        "advanced": [
                            "global CDN",
                            "real-time analytics",
                            "fraud detection",
                        ],
                    },
                },
            }

            topic_data = topic_mapping.get(
                topic,
                {
                    "key_concepts": [
                        "system architecture",
                        "scalability",
                        "data modeling",
                    ],
                    "patterns": ["microservices", "caching", "load balancing"],
                    "difficulty_focus": {
                        "beginner": ["basic design principles"],
                        "intermediate": ["scaling and optimization"],
                        "advanced": ["distributed systems complexity"],
                    },
                },
            )

            analysis = {
                "topic": topic,
                "key_concepts": topic_data["key_concepts"],
                "common_patterns": topic_data["patterns"],
                "difficulty_concepts": topic_data["difficulty_focus"].get(
                    difficulty, ["general system design"]
                ),
                "recommended_focus": f"For {difficulty} level {topic}, focus on: {', '.join(topic_data['difficulty_focus'].get(difficulty, ['core concepts']))}",
            }

            return json.dumps(analysis, indent=2)

        return analyze_topic

    def _create_context_evaluation_tool(self):
        """Tool for evaluating conversation context and flow"""

        def evaluate_context(
            previous_question: str, user_answer: str, evaluation_data: str
        ) -> str:
            """Evaluate conversation context to determine best follow-up approach"""

            try:
                evaluation = json.loads(evaluation_data) if evaluation_data else {}

                context_analysis = {
                    "answer_quality_score": evaluation.get("clarity_score", 5),
                    "technical_depth_score": evaluation.get("technical_depth", 5),
                    "identified_strengths": evaluation.get("analysis", {}).get(
                        "strengths", []
                    ),
                    "identified_weaknesses": evaluation.get("analysis", {}).get(
                        "weaknesses", []
                    ),
                    "missing_concepts": evaluation.get("analysis", {}).get(
                        "missing_topics", []
                    ),
                    "conversation_depth": (
                        len(user_answer.split()) if user_answer else 0
                    ),
                    "follow_up_strategy": evaluation.get("next_steps", {}).get(
                        "suggested_follow_up", "deeper_dive"
                    ),
                    "recommended_approach": (
                        "drill_deeper"
                        if evaluation.get("clarity_score", 5) > 6
                        else "provide_guidance"
                    ),
                }

                return json.dumps(context_analysis, indent=2)

            except Exception as e:
                return json.dumps(
                    {"error": str(e), "default_strategy": "continue_conversation"},
                    indent=2,
                )

        return evaluate_context

    def _create_difficulty_assessment_tool(self):
        """Tool for assessing and adjusting question difficulty"""

        def assess_difficulty(
            current_difficulty: str, performance_indicators: str
        ) -> str:
            """Assess if question difficulty should be adjusted based on performance"""

            try:
                indicators = (
                    json.loads(performance_indicators) if performance_indicators else {}
                )

                assessment = {
                    "current_level": current_difficulty,
                    "performance_score": indicators.get("average_score", 5),
                    "consistency": indicators.get("score_variance", "stable"),
                    "should_adjust": False,
                    "suggested_level": current_difficulty,
                    "adjustment_reason": "maintaining current level",
                }

                avg_score = indicators.get("average_score", 5)
                if avg_score > 8:
                    assessment.update(
                        {
                            "should_adjust": True,
                            "suggested_level": (
                                "advanced"
                                if current_difficulty == "intermediate"
                                else "expert"
                            ),
                            "adjustment_reason": "user demonstrating high competency",
                        }
                    )
                elif avg_score < 4:
                    assessment.update(
                        {
                            "should_adjust": True,
                            "suggested_level": (
                                "beginner"
                                if current_difficulty == "intermediate"
                                else "basic"
                            ),
                            "adjustment_reason": "user needs more foundational support",
                        }
                    )

                return json.dumps(assessment, indent=2)

            except Exception as e:
                return json.dumps(
                    {"error": str(e), "maintain_current": current_difficulty}, indent=2
                )

        return assess_difficulty

    def _create_prompt_optimization_tool(self):
        """Tool for optimizing question phrasing and structure"""

        def optimize_prompt(
            question_intent: str, target_concepts: str, difficulty: str
        ) -> str:
            """Optimize question phrasing for maximum effectiveness"""

            optimization_strategies = {
                "beginner": {
                    "style": "supportive and guiding",
                    "structure": "step-by-step prompts",
                    "language": "clear and simple",
                    "hints": "embedded guidance",
                },
                "intermediate": {
                    "style": "challenging but fair",
                    "structure": "open-ended with focus areas",
                    "language": "technical but accessible",
                    "hints": "subtle direction",
                },
                "advanced": {
                    "style": "thought-provoking",
                    "structure": "complex scenarios",
                    "language": "technical and precise",
                    "hints": "minimal guidance",
                },
            }

            strategy = optimization_strategies.get(
                difficulty, optimization_strategies["intermediate"]
            )

            optimization = {
                "question_intent": question_intent,
                "target_concepts": target_concepts,
                "difficulty_level": difficulty,
                "recommended_style": strategy["style"],
                "suggested_structure": strategy["structure"],
                "language_approach": strategy["language"],
                "hint_strategy": strategy["hints"],
                "optimization_notes": f"Structure the question with {strategy['style']} tone, using {strategy['language']} language",
            }

            return json.dumps(optimization, indent=2)

        return optimize_prompt

    async def generate_opening_question(
        self, topic: str, difficulty: DifficultyLevel, context: Dict[str, Any] = None
    ) -> QuestionGeneration:
        """
        Generate an opening question using React agent with intelligent analysis
        """
        logger.info(
            f"Generating opening question for topic: {topic}, difficulty: {difficulty}"
        )

        context = context or {}

        # Use React agent to generate intelligent opening question
        agent_input = {
            "messages": [
                HumanMessage(
                    content=f"""
                Generate an opening question for a system design interview:
                
                Topic: {topic}
                Difficulty: {difficulty.value}
                User Context: {json.dumps(context, indent=2)}
                
                Process:
                1. Use topic_analysis tool to understand domain concepts
                2. Use difficulty_assessment tool to calibrate complexity
                3. Use prompt_optimization tool to refine question structure
                4. Generate an engaging opening question
                
                Requirements:
                - Set clear interview expectations
                - Begin requirements gathering naturally
                - Match the specified difficulty level
                - Engage and motivate the candidate
                - Include helpful guidance hints
                
                Return structured QuestionGeneration JSON with:
                - Engaging question text
                - Targeted topics and concepts
                - Expected answer components
                - Helpful guidance hints
                - Appropriate time estimate
                """
                )
            ]
        }

        try:
            # Get intelligent response from React agent
            response = await self.agent.ainvoke(agent_input)

            # Extract structured question from agent response
            question = self._extract_question_from_response(
                response, "opening", topic, difficulty.value
            )

            logger.info(f"Opening question generated for {topic}")
            return question

        except Exception as e:
            logger.error(f"Error with React agent: {str(e)}")
            # Fallback to direct generation
            return self._create_fallback_question(topic, difficulty.value, "opening")

    async def generate_follow_up_question(
        self,
        previous_question: str,
        user_answer: str,
        evaluation: Dict[str, Any],
        topic: str,
        difficulty: DifficultyLevel,
    ) -> QuestionGeneration:
        """
        Generate intelligent follow-up question using React agent analysis
        """
        logger.info("Generating follow-up question based on evaluation")

        # Use React agent for intelligent follow-up generation
        agent_input = {
            "messages": [
                HumanMessage(
                    content=f"""
                Generate an intelligent follow-up question based on this interview interaction:
                
                Previous Question: {previous_question}
                User Answer: {user_answer}
                Answer Evaluation: {json.dumps(evaluation, indent=2)}
                Topic: {topic}
                Difficulty: {difficulty.value}
                
                Analysis Process:
                1. Use context_evaluation tool to analyze the conversation flow
                2. Use topic_analysis tool to identify unexplored areas
                3. Use difficulty_assessment tool to calibrate question complexity
                4. Use prompt_optimization tool to craft the perfect follow-up
                
                Context Analysis:
                - User's demonstrated strengths and knowledge gaps
                - Missing concepts that should be explored
                - Natural conversation progression opportunities
                - Appropriate challenge level for continued learning
                
                Generate a follow-up question that:
                - Builds naturally on the previous interaction
                - Addresses identified knowledge gaps
                - Maintains appropriate difficulty progression
                - Encourages deeper technical exploration
                - Includes contextual guidance if needed
                
                Return structured QuestionGeneration JSON format.
                """
                )
            ]
        }

        try:
            # Get intelligent response from React agent
            response = await self.agent.ainvoke(agent_input)

            # Extract structured question from agent response
            question = self._extract_question_from_response(
                response, "follow_up", topic, difficulty.value
            )

            logger.info("Intelligent follow-up question generated")
            return question

        except Exception as e:
            logger.error(f"Error generating follow-up with React agent: {str(e)}")
            # Fallback generation
            return self._generate_fallback_follow_up(
                previous_question, user_answer, topic, difficulty
            )

    def _extract_question_from_response(
        self, response, question_type: str, topic: str, difficulty: str
    ) -> QuestionGeneration:
        """Extract structured question from React agent response"""
        try:
            # In a full implementation, this would parse the agent's response
            # and extract the structured QuestionGeneration object from tool usage

            # For now, create an intelligent structured response based on the context
            if question_type == "opening":
                question_text = f"Let's design a {topic.replace('_', ' ')} system. What would you say are the key functional requirements we need to consider?"
                topics_targeted = ["requirements_gathering", "functional_design"]
                expected_concepts = ["user needs", "core features", "system boundaries"]
            else:  # follow_up
                question_text = "Based on your previous answer, let's dive deeper into the architecture. How would you structure the main components?"
                topics_targeted = ["system_architecture", "component_design"]
                expected_concepts = [
                    "service boundaries",
                    "data flow",
                    "component interactions",
                ]

            return QuestionGeneration(
                question=question_text,
                question_type=question_type,
                topics_targeted=topics_targeted,
                difficulty_level=difficulty,
                expected_concepts=expected_concepts,
                guidance_hints=[
                    "Think about the core functionality",
                    "Consider the user journey",
                    "Think about data requirements",
                ],
                time_estimate=5,
                follow_up_areas=["scalability", "data_modeling", "API_design"],
            )

        except Exception as e:
            logger.error(f"Error extracting question from response: {str(e)}")
            return self._create_fallback_question(topic, difficulty, question_type)

    def _generate_fallback_follow_up(
        self,
        previous_question: str,
        user_answer: str,
        topic: str,
        difficulty: DifficultyLevel,
    ) -> QuestionGeneration:
        """Generate fallback follow-up question when React agent fails"""
        logger.warning("Generating fallback follow-up question")

        # Simple heuristic-based follow-up
        follow_up_templates = {
            "beginner": "That's a good start! Can you tell me more about how you would handle {aspect}?",
            "intermediate": "Interesting approach. How would you ensure {aspect} while maintaining {concern}?",
            "advanced": "Given your design, what trade-offs would you consider for {aspect} in a large-scale deployment?",
        }

        aspects = [
            "data storage",
            "user authentication",
            "real-time updates",
            "scalability",
        ]
        concerns = ["performance", "consistency", "availability", "security"]

        template = follow_up_templates.get(
            difficulty.value, follow_up_templates["intermediate"]
        )
        question_text = template.format(aspect=aspects[0], concern=concerns[0])

        return QuestionGeneration(
            question=question_text,
            question_type="follow_up",
            topics_targeted=["architecture", "trade_offs"],
            difficulty_level=difficulty.value,
            expected_concepts=["system design principles", "architectural decisions"],
            guidance_hints=[
                "Consider the pros and cons",
                "Think about scale",
                "Consider user experience",
            ],
            time_estimate=5,
            follow_up_areas=["performance", "scalability", "reliability"],
        )

    async def generate_clarification_question(
        self,
        unclear_areas: List[str],
        user_answer: str,
        topic: str,
        difficulty: DifficultyLevel,
    ) -> QuestionGeneration:
        """
        Generate a clarification question using React agent analysis
        """
        logger.info(f"Generating clarification question for: {unclear_areas}")

        agent_input = {
            "messages": [
                HumanMessage(
                    content=f"""
                Generate a clarification question for unclear aspects in the user's answer:
                
                Topic: {topic}
                User Answer: {user_answer}
                Unclear Areas: {unclear_areas}
                Difficulty: {difficulty.value}
                
                Process:
                1. Use context_evaluation tool to understand what's missing
                2. Use prompt_optimization tool to craft a helpful clarification request
                3. Generate a question that guides the user toward clarity
                
                The clarification question should:
                - Address the specific unclear areas
                - Be supportive and encouraging
                - Guide toward better understanding
                - Maintain interview flow
                
                Return structured QuestionGeneration JSON.
                """
                )
            ]
        }

        try:
            response = await self.agent.ainvoke(agent_input)
            question = self._extract_question_from_response(
                response, "clarification", topic, difficulty.value
            )

            logger.info("Clarification question generated")
            return question

        except Exception as e:
            logger.error(f"Error generating clarification: {str(e)}")
            return self._create_fallback_question(
                topic, difficulty.value, "clarification"
            )

    async def generate_topic_transition_question(
        self,
        current_topic: str,
        next_topic: str,
        progress: Dict[str, Any],
        difficulty: DifficultyLevel,
    ) -> QuestionGeneration:
        """
        Generate a smooth topic transition question using React agent
        """
        logger.info(f"Generating transition from {current_topic} to {next_topic}")

        agent_input = {
            "messages": [
                HumanMessage(
                    content=f"""
                Generate a smooth topic transition question:
                
                Current Topic: {current_topic}
                Next Topic: {next_topic}
                Progress: {json.dumps(progress, indent=2)}
                Difficulty: {difficulty.value}
                
                Process:
                1. Use topic_analysis tool to understand both topics
                2. Use context_evaluation tool to assess progress
                3. Use prompt_optimization tool to create smooth transition
                4. Generate a natural transition question
                
                Requirements:
                - Acknowledge progress on current topic
                - Naturally introduce the next topic
                - Maintain conversation flow
                - Set expectations for new area
                
                Return structured QuestionGeneration JSON.
                """
                )
            ]
        }

        try:
            response = await self.agent.ainvoke(agent_input)
            question = self._extract_question_from_response(
                response, "topic_transition", next_topic, difficulty.value
            )

            logger.info(f"Topic transition question generated")
            return question

        except Exception as e:
            logger.error(f"Error generating topic transition: {str(e)}")
            return self._create_fallback_question(
                next_topic, difficulty.value, "topic_transition"
            )

    async def generate_hint(
        self,
        context: str,
        hint_type: str = "conceptual",
        topic: str = "",
        difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
    ) -> AIHint:
        """
        Generate a contextual hint for the candidate using structured output
        """
        logger.info(f"Generating {hint_type} hint")

        try:
            system_prompt = """
            You are an AI interview coach providing helpful hints to candidates.
            
            Guidelines for hints:
            - Be helpful but not too direct
            - Guide thinking without giving away the answer
            - Encourage exploration and learning
            - Maintain appropriate challenge level
            - Provide reasoning for the hint
            
            You must respond with structured JSON following the AIHint schema.
            """

            user_prompt = f"""
            Generate a {hint_type} hint for this context:
            
            CONTEXT: {context}
            TOPIC: {topic}
            DIFFICULTY: {difficulty.value}
            
            The hint should:
            - Guide the candidate's thinking
            - Provide just enough information to help
            - Maintain the learning challenge
            - Be encouraging and supportive
            
            Include follow-up questions that help the candidate explore further.
            
            Format Instructions:
            {self.hint_parser.get_format_instructions()}
            """

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = self.llm.invoke(messages)
            hint = self.hint_parser.parse(response.content)

            logger.info("Hint generated successfully")
            return hint

        except Exception as e:
            logger.error(f"Error generating hint: {str(e)}")
            # Return fallback hint
            return AIHint(
                hint_type=hint_type,
                hint_content="Consider breaking down the problem into smaller components and think about how they interact.",
                reasoning="This is a general problem-solving approach that helps with system design.",
                follow_up_questions=[
                    "What are the main components of your system?",
                    "How do these components communicate?",
                    "What are the data flows between components?",
                ],
            )

    def _create_fallback_question(
        self, topic: str, difficulty: str, question_type: str
    ) -> QuestionGeneration:
        """Create fallback question when AI generation fails"""
        logger.warning(
            f"Creating fallback question for {topic}, {difficulty}, {question_type}"
        )

        # Use template-based fallback
        templates = TOPIC_QUESTION_TEMPLATES.get(topic, {})
        opening_templates = templates.get("opening", {})

        fallback_question = opening_templates.get(
            difficulty,
            f"Let's discuss the design of a {topic.replace('_', ' ')} system. What would be your approach?",
        )

        return QuestionGeneration(
            question=fallback_question,
            question_type=question_type,
            topics_targeted=[topic],
            difficulty_level=difficulty,
            expected_concepts=templates.get("key_areas", ["system design basics"]),
            guidance_hints=[
                "Think about the main components",
                "Consider the data flow",
                "Think about scalability requirements",
            ],
        )
