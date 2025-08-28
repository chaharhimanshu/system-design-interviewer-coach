"""
Main Orchestrator Agent
OpenAI Assistant-powered agent that coordinates all specialized agents using React pattern
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, END

from app.domain.entities.session import (
    InterviewSession,
    SessionStatus,
    DifficultyLevel,
    MessageRole,
    MessageType,
)
from app.agents.models.output_schemas import (
    QuestionGeneration,
    AnswerEvaluation,
    FeedbackResponse,
    DifficultyAdjustment,
    SessionSummary,
)
from app.agents.specialized.question_generator import QuestionGeneratorAgent
from app.agents.specialized.answer_evaluator import AnswerEvaluatorAgent
from app.agents.specialized.feedback_provider import FeedbackProviderAgent
from app.agents.specialized.difficulty_adaptor import DifficultyAdaptorAgent
from app.agents.memory.conversation_memory import ConversationMemory
from app.agents.prompts.orchestrator_prompts import (
    ORCHESTRATOR_SYSTEM_PROMPTS,
    ACTION_DETERMINATION_PROMPTS,
    INTERVIEW_PHASES,
    ACTION_PRIORITY_MATRIX,
)
from app.infrastructure.config.settings import get_settings
from app.shared.logging import get_logger

logger = get_logger(__name__)


class InterviewAction(Enum):
    """Possible interview actions"""

    GENERATE_FOLLOW_UP = "generate_follow_up"
    GENERATE_CLARIFICATION = "generate_clarification"
    GENERATE_TOPIC_TRANSITION = "generate_topic_transition"
    PROVIDE_FEEDBACK = "provide_feedback"
    PROVIDE_HINT = "provide_hint"
    ADJUST_DIFFICULTY = "adjust_difficulty"
    GENERATE_SUMMARY = "generate_summary"
    SESSION_COMPLETION = "session_completion"


class InterviewPhase(Enum):
    """Interview phases"""

    OPENING = "opening"
    ARCHITECTURE = "architecture"
    DEEP_DIVE = "deep_dive"
    OPTIMIZATION = "optimization"
    WRAP_UP = "wrap_up"


class ActionDecision(BaseModel):
    """Structured action decision from orchestrator"""

    recommended_action: InterviewAction
    reasoning: str
    confidence_level: float = Field(ge=0, le=1)
    alternative_actions: List[InterviewAction]
    specific_context: Dict[str, Any]


class MainOrchestrator:
    """
    Main Orchestrator Agent using OpenAI Assistant with React pattern
    Coordinates all specialized agents for intelligent interview flow
    """

    def __init__(self):
        self.settings = get_settings()

        # Initialize OpenAI model for orchestration
        self.llm = ChatOpenAI(
            model=self.settings.OPENAI_MODEL,
            temperature=0.5,  # Balanced temperature for decision making
            api_key=self.settings.OPENAI_API_KEY,
            max_tokens=self.settings.OPENAI_MAX_TOKENS,
        )

        # Initialize specialized agents
        self.question_generator = QuestionGeneratorAgent()
        self.answer_evaluator = AnswerEvaluatorAgent()
        self.feedback_provider = FeedbackProviderAgent()
        self.difficulty_adaptor = DifficultyAdaptorAgent()

        # Initialize memory system
        self.memory = ConversationMemory()

        # Create action decision parser
        self.action_parser = PydanticOutputParser(pydantic_object=ActionDecision)

        # Create React agent workflow
        self.agent = self._create_react_agent()

        # Session state tracking
        self.current_sessions: Dict[UUID, Dict[str, Any]] = {}

        logger.info("MainOrchestrator initialized with React agent pattern")

    def _create_react_agent(self) -> create_react_agent:
        """Create React agent for intelligent decision making"""

        # Define tools for the React agent
        tools = [
            self._create_evaluation_tool(),
            self._create_question_generation_tool(),
            self._create_feedback_tool(),
            self._create_difficulty_assessment_tool(),
            self._create_memory_analysis_tool(),
        ]

        # Create system prompt for React agent
        system_prompt = (
            ORCHESTRATOR_SYSTEM_PROMPTS["base"]
            + """
        
        You have access to specialized tools for:
        - evaluate_answer: Evaluate user responses
        - generate_question: Generate contextual questions
        - provide_feedback: Generate personalized feedback
        - assess_difficulty: Analyze difficulty appropriateness
        - analyze_memory: Get conversation insights
        
        Use these tools to make informed decisions about interview flow.
        Always use tools to gather information before making decisions.
        
        Your goal is to create the best possible learning experience.
        """
        )

        # Create React agent
        agent = create_react_agent(
            model=self.llm, tools=tools, state_modifier=system_prompt
        )

        return agent

    async def start_interview(
        self, session: InterviewSession, user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start a new interview session using React agent
        """
        session_id = session.session_id
        logger.info(
            f"Starting interview session {session_id} for topic {session.topic}"
        )

        # Initialize session state
        self.current_sessions[session_id] = {
            "session": session,
            "topic": session.topic,
            "difficulty": session.difficulty_level,
            "phase": InterviewPhase.OPENING,
            "start_time": datetime.now(),
            "questions_asked": 0,
            "topics_covered": [],
            "performance_history": [],
            "user_context": user_context or {},
        }

        # Initialize memory for this session
        await self.memory.initialize_session(
            session_id, session.topic, session.difficulty_level.value
        )

        try:
            # Use React agent to generate opening question
            agent_input = {
                "messages": [
                    HumanMessage(
                        content=f"""
                    Start a new system design interview session:
                    
                    Session ID: {session_id}
                    Topic: {session.topic}
                    Difficulty: {session.difficulty_level.value}
                    User Context: {json.dumps(user_context or {}, indent=2)}
                    
                    Generate an opening question that:
                    1. Sets clear expectations
                    2. Begins requirements gathering
                    3. Matches the difficulty level
                    4. Engages the candidate
                    
                    Use the generate_question tool to create the opening question.
                    """
                    )
                ]
            }

            # Get response from React agent
            response = await self.agent.ainvoke(agent_input)

            # Extract the generated question
            opening_question = self._extract_question_from_response(response)

            # Update session state
            self.current_sessions[session_id]["questions_asked"] += 1
            self.current_sessions[session_id][
                "last_question"
            ] = opening_question.question

            # Store the opening question in memory
            await self.memory.add_interaction(
                session_id=session_id,
                question=opening_question.question,
                context=opening_question.dict(),
                expected_topics=opening_question.expected_concepts,
            )

            logger.info(f"Interview started successfully for session {session_id}")

            return {
                "question": opening_question.question,
                "context": f"Starting {session.difficulty_level.value} level interview on {session.topic}",
                "stage": InterviewPhase.OPENING.value,
                "expected_topics": opening_question.expected_concepts,
                "guidance": opening_question.guidance_hints,
                "session_id": str(session_id),
            }

        except Exception as e:
            logger.error(f"Error starting interview: {str(e)}")
            # Return fallback opening question
            return {
                "question": f"Let's design a {session.topic.replace('_', ' ')} system. What would you say are the key requirements we should consider?",
                "context": f"Starting {session.difficulty_level.value} level interview on {session.topic}",
                "stage": InterviewPhase.OPENING.value,
                "expected_topics": ["requirements", "architecture", "scalability"],
                "guidance": [
                    "Think about user needs",
                    "Consider scalability",
                    "Think about data flow",
                ],
                "session_id": str(session_id),
                "fallback": True,
            }

    async def process_user_answer(
        self, session_id: UUID, user_answer: str, message_type: str = "answer"
    ) -> Dict[str, Any]:
        """
        Process user answer using React agent to determine next action
        """
        logger.info(f"Processing user answer for session {session_id}")

        if session_id not in self.current_sessions:
            raise ValueError(f"Session {session_id} not found")

        session_state = self.current_sessions[session_id]

        try:
            # Use React agent to process the answer
            agent_input = {
                "messages": [
                    HumanMessage(
                        content=f"""
                    Process this user answer in a system design interview:
                    
                    Session ID: {session_id}
                    Topic: {session_state['topic']}
                    Difficulty: {session_state['difficulty'].value}
                    Current Phase: {session_state['phase'].value}
                    Previous Question: {session_state.get('last_question', 'N/A')}
                    
                    User Answer: {user_answer}
                    
                    Steps to take:
                    1. Use evaluate_answer tool to assess the response
                    2. Use analyze_memory tool to get conversation context
                    3. Use assess_difficulty tool to check if difficulty is appropriate
                    4. Determine the best next action based on the evaluation
                    5. Execute the appropriate action (generate question, provide feedback, etc.)
                    
                    Focus on creating the best learning experience for the candidate.
                    """
                    )
                ]
            }

            # Get response from React agent
            response = await self.agent.ainvoke(agent_input)

            # Extract and process the agent's decision
            processed_response = await self._process_agent_response(
                response, session_id, user_answer
            )

            # Update session state
            self._update_session_state(session_id, user_answer, processed_response)

            logger.info(f"User answer processed successfully for session {session_id}")

            return processed_response

        except Exception as e:
            logger.error(f"Error processing user answer: {str(e)}")
            # Return fallback response
            return await self._generate_fallback_response(
                session_id, user_answer, str(e)
            )

    async def get_session_insights(self, session_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive session insights using memory analysis
        """
        logger.info(f"Getting session insights for {session_id}")

        if session_id not in self.current_sessions:
            raise ValueError(f"Session {session_id} not found")

        try:
            # Get memory insights
            context = await self.memory.get_session_context(session_id)

            # Add orchestrator-level insights
            session_state = self.current_sessions[session_id]
            orchestrator_insights = {
                "session_duration": (
                    datetime.now() - session_state["start_time"]
                ).total_seconds()
                / 60,
                "questions_asked": session_state["questions_asked"],
                "current_phase": session_state["phase"].value,
                "topics_covered": session_state["topics_covered"],
                "phase_progression": self._analyze_phase_progression(session_state),
            }

            return {
                "memory_insights": context,
                "orchestrator_insights": orchestrator_insights,
                "recommendations": self._generate_session_recommendations(
                    session_state, context
                ),
            }

        except Exception as e:
            logger.error(f"Error getting session insights: {str(e)}")
            return {
                "error": "Unable to retrieve session insights",
                "session_id": str(session_id),
            }

    def _create_evaluation_tool(self):
        """Create tool for answer evaluation"""

        async def evaluate_answer(
            question: str, answer: str, topic: str, difficulty: str, context: str = "{}"
        ):
            """Evaluate user's answer using the Answer Evaluator Agent"""
            try:
                evaluation = await self.answer_evaluator.evaluate_answer(
                    question=question,
                    answer=answer,
                    topic=topic,
                    difficulty=DifficultyLevel(difficulty),
                    context=json.loads(context) if context else {},
                )
                return evaluation.dict()
            except Exception as e:
                logger.error(f"Error in evaluation tool: {str(e)}")
                return {"error": str(e)}

        return evaluate_answer

    def _create_question_generation_tool(self):
        """Create tool for question generation"""

        async def generate_question(
            question_type: str, topic: str, difficulty: str, context: str = "{}"
        ):
            """Generate contextual question using Question Generator Agent"""
            try:
                ctx = json.loads(context) if context else {}

                if question_type == "opening":
                    question = await self.question_generator.generate_opening_question(
                        topic=topic, difficulty=DifficultyLevel(difficulty), context=ctx
                    )
                elif question_type == "follow_up":
                    question = (
                        await self.question_generator.generate_follow_up_question(
                            previous_question=ctx.get("previous_question", ""),
                            user_answer=ctx.get("user_answer", ""),
                            evaluation=ctx.get("evaluation", {}),
                            topic=topic,
                            difficulty=DifficultyLevel(difficulty),
                        )
                    )
                else:
                    question = await self.question_generator.generate_opening_question(
                        topic=topic, difficulty=DifficultyLevel(difficulty)
                    )

                return question.dict()
            except Exception as e:
                logger.error(f"Error in question generation tool: {str(e)}")
                return {"error": str(e)}

        return generate_question

    def _create_feedback_tool(self):
        """Create tool for feedback generation"""

        async def provide_feedback(
            evaluation: str, feedback_type: str = "constructive", context: str = "{}"
        ):
            """Generate feedback using Feedback Provider Agent"""
            try:
                feedback = await self.feedback_provider.generate_feedback(
                    evaluation=json.loads(evaluation),
                    feedback_style=feedback_type,
                    context=json.loads(context) if context else {},
                )
                return feedback.dict()
            except Exception as e:
                logger.error(f"Error in feedback tool: {str(e)}")
                return {"error": str(e)}

        return provide_feedback

    def _create_difficulty_assessment_tool(self):
        """Create tool for difficulty assessment"""

        async def assess_difficulty(performance_data: str, current_difficulty: str):
            """Assess if difficulty should be adjusted"""
            try:
                assessment = await self.difficulty_adaptor.should_adjust_difficulty(
                    performance_history=json.loads(performance_data),
                    current_difficulty=DifficultyLevel(current_difficulty),
                )
                return assessment.dict()
            except Exception as e:
                logger.error(f"Error in difficulty assessment tool: {str(e)}")
                return {"error": str(e)}

        return assess_difficulty

    def _create_memory_analysis_tool(self):
        """Create tool for memory analysis"""

        async def analyze_memory(session_id: str):
            """Analyze conversation memory for insights"""
            try:
                context = await self.memory.get_session_context(UUID(session_id))
                return context
            except Exception as e:
                logger.error(f"Error in memory analysis tool: {str(e)}")
                return {"error": str(e)}

        return analyze_memory

    def _extract_question_from_response(self, response) -> QuestionGeneration:
        """Extract generated question from agent response"""
        # For now, return a structured fallback
        # In a full implementation, this would parse the agent's tool usage results
        return QuestionGeneration(
            question="What are the key requirements for this system?",
            question_type="opening",
            topics_targeted=["requirements"],
            difficulty_level="intermediate",
            expected_concepts=[
                "functional requirements",
                "non-functional requirements",
            ],
            guidance_hints=["Think about users", "Consider scale", "Think about data"],
        )

    async def _process_agent_response(
        self, response, session_id: UUID, user_answer: str
    ) -> Dict[str, Any]:
        """Process the React agent's response to determine the final output"""
        # Extract the agent's decision and tool usage results
        # This would involve parsing the agent's response and extracting tool results

        # For now, generate a structured response based on simple heuristics
        session_state = self.current_sessions[session_id]

        # Generate follow-up question as default action
        follow_up = await self.question_generator.generate_follow_up_question(
            previous_question=session_state.get("last_question", ""),
            user_answer=user_answer,
            evaluation={"clarity_score": 7.0},  # Mock evaluation
            topic=session_state["topic"],
            difficulty=session_state["difficulty"],
        )

        return {
            "type": "follow_up",
            "message": follow_up.question,
            "context": follow_up.dict(),
            "focus_areas": follow_up.topics_targeted,
            "session_id": str(session_id),
        }

    async def _generate_fallback_response(
        self, session_id: UUID, user_answer: str, error: str
    ) -> Dict[str, Any]:
        """Generate fallback response when agent processing fails"""
        session_state = self.current_sessions[session_id]

        return {
            "type": "fallback",
            "message": "Thank you for your response. Can you elaborate on your approach to handling scalability?",
            "context": f"Fallback response due to: {error}",
            "focus_areas": ["scalability", "architecture"],
            "session_id": str(session_id),
            "fallback": True,
        }

    def _update_session_state(
        self, session_id: UUID, user_answer: str, response: Dict[str, Any]
    ):
        """Update session state based on the interaction"""
        session_state = self.current_sessions[session_id]
        session_state["questions_asked"] += 1

        if "evaluation" in response:
            session_state["performance_history"].append(response["evaluation"])

        # Update last question
        if "message" in response:
            session_state["last_question"] = response["message"]

    def _analyze_phase_progression(
        self, session_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze how the interview is progressing through phases"""
        return {
            "current_phase": session_state["phase"].value,
            "phase_duration": 0,  # Calculate based on timestamps
            "ready_for_next_phase": session_state["questions_asked"] > 3,
        }

    def _generate_session_recommendations(
        self, session_state: Dict[str, Any], context: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for the session"""
        recommendations = []

        if session_state["questions_asked"] > 8:
            recommendations.append("Consider moving to wrap-up phase")

        if len(session_state["topics_covered"]) < 3:
            recommendations.append("Explore more topic areas")

        return recommendations

    async def cleanup_session(self, session_id: UUID) -> None:
        """Cleanup session resources"""
        if session_id in self.current_sessions:
            del self.current_sessions[session_id]
        await self.memory.cleanup_session(session_id)
        logger.info(f"Cleaned up session {session_id}")
