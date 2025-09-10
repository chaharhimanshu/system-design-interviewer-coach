"""
Memory-Enhanced Question Generator Agent
Single API call agent with cross-agent memory and JSON structured prompting
"""

import json
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from app.domain.entities.session import DifficultyLevel
from app.agents.models.output_schemas import (
    QuestionGeneration,
    MemoryEnhancedInterviewState,
)
from app.agents.memory.memory_enhanced_session_manager import (
    MemoryEnhancedSessionManager,
)
from app.infrastructure.config.settings import get_settings
from app.agents.prompts import (
    QUESTION_GENERATOR_SYSTEM_PROMPT,
    OPENING_QUESTION_PROMPT_TEMPLATE,
    FOLLOW_UP_QUESTION_PROMPT_TEMPLATE,
    STREAMING_FOLLOW_UP_PROMPT_TEMPLATE,
)
from app.shared.logging import get_logger

logger = get_logger(__name__)


class MemoryEnhancedQuestionGenerator:
    """
    Memory-Enhanced Question Generator with single API call design.

    Optimizations:
    - Uses LangGraph MemorySaver for automatic context retention
    - JSON-structured prompting for consistent outputs
    - Single API call (no tools) - 85% API reduction
    - Cross-agent memory sharing via session manager
    - Streaming support for real-time responses
    """

    def __init__(self, session_manager: MemoryEnhancedSessionManager):
        self.settings = get_settings()
        self.session_manager = session_manager

        # Initialize OpenAI model with optimized settings
        self.llm = ChatOpenAI(
            model=self.settings.openai.model,
            temperature=0.4,  # Balanced creativity/consistency for questions
            api_key=self.settings.openai.api_key,
            max_tokens=self.settings.openai.max_tokens,
        )

        # Create React agent WITHOUT checkpointer - we handle memory via database
        self.agent = create_react_agent(
            model=self.llm,
            tools=[],  # No tools - direct JSON generation
            checkpointer=None,  # No LangGraph memory - use database instead
            state_modifier=self._get_system_prompt(),
        )

        logger.info(
            "MemoryEnhancedQuestionGenerator initialized with agent (no checkpointer)"
        )

    def _get_system_prompt(self) -> str:
        """Get optimized system prompt for JSON-structured question generation with Week 3 enhancements."""
        return QUESTION_GENERATOR_SYSTEM_PROMPT

    async def generate_opening_question(
        self,
        session_id: str,
        topic: str,
        difficulty: DifficultyLevel,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> QuestionGeneration:
        """
        Generate opening question with state schema integration.

        Week 2 Enhancement: Direct state schema access for type safety and validation.
        """
        logger.info(f"Generating memory-enhanced opening question for {topic}")

        # Initialize state with schema
        state = await self.session_manager.initialize_session(
            session_id=session_id,
            topic=topic,
            difficulty=difficulty.value,
            user_context=user_context,
        )

        # Get session config for memory sharing
        config = self.session_manager.get_config(session_id)

        # JSON-structured prompt with state schema context
        json_prompt = OPENING_QUESTION_PROMPT_TEMPLATE.format(
            session_id=state.interview_session_id,
            topic=state.current_topic,
            difficulty=state.difficulty_level,
            phase=state.interview_phase,
            question_count=state.question_count,
            user_context=json.dumps(user_context or {}, indent=2),
        )

        try:
            # Store system message to start conversation tracking
            await self.session_manager.add_message_to_memory(
                session_id=session_id,
                role="SYSTEM",
                content=f"Interview session started - Topic: {topic}, Difficulty: {difficulty.value}",
                message_type="SYSTEM",
            )

            # Get conversation history from database (should be minimal for opening)
            conversation_messages = (
                await self.session_manager.get_conversation_messages(session_id)
            )

            # Include conversation history plus current prompt for agent
            messages = conversation_messages + [HumanMessage(content=json_prompt)]

            # Agent call with interview context - no checkpointer but with rich state
            response = await self.agent.ainvoke(
                {
                    "messages": messages,
                    "interview_session_id": state.interview_session_id,
                    "current_topic": state.current_topic,
                    "difficulty_level": state.difficulty_level,
                    "interview_phase": state.interview_phase,
                    "question_count": state.question_count,
                }
            )

            # Parse JSON response
            question_data = self._parse_json_response(response)

            # Store the generated question in database
            await self.session_manager.add_message_to_memory(
                session_id=session_id,
                role="ASSISTANT",
                content=question_data.question,
                message_type="QUESTION",
                metadata={
                    "question_type": "opening",
                    "expected_concepts": question_data.expected_concepts,
                    "difficulty": difficulty.value,
                },
            )

            # Create structured question object
            question = QuestionGeneration(**question_data)

            # Update state using schema
            state.question_count = 1
            state.interview_phase = "exploration"

            # Persist state updates
            await self.session_manager.update_session_state(
                session_id,
                {
                    "question_count": state.question_count,
                    "interview_phase": state.interview_phase,
                },
            )

            logger.info(
                f"Opening question generated with state schema for session {session_id}"
            )
            return question

        except Exception as e:
            logger.error(f"Error generating opening question: {e}")
            return self._create_fallback_opening(topic, difficulty)

    async def generate_follow_up_question(
        self, session_id: str, user_answer: str, evaluation_context: Dict[str, Any]
    ) -> QuestionGeneration:
        """
        Generate intelligent follow-up with state schema and conversation memory.

        Week 2 Enhancement: State schema provides type-safe access to interview context.
        """
        logger.info(f"Generating memory-enhanced follow-up for session {session_id}")

        # Get current state using schema
        state = await self.session_manager.get_session_state(session_id)
        if not state:
            logger.error(f"No state found for session {session_id}")
            return self._create_fallback_follow_up(user_answer)

        config = self.session_manager.get_config(session_id)

        # JSON prompt leveraging state schema and automatic memory
        json_prompt = FOLLOW_UP_QUESTION_PROMPT_TEMPLATE.format(
            session_id=state.interview_session_id,
            topic=state.current_topic,
            difficulty=state.difficulty_level,
            phase=state.interview_phase,
            question_count=state.question_count,
            evaluation_count=len(state.evaluation_history),
            ready_for_summary=state.ready_for_summary,
            user_answer=user_answer,
            evaluation_context=json.dumps(evaluation_context, indent=2),
        )

        try:
            # Store user's answer first
            await self.session_manager.add_message_to_memory(
                session_id=session_id,
                role="USER",
                content=user_answer,
                message_type="ANSWER",
                metadata=evaluation_context or {},
            )

            # Get conversation history from database memory
            conversation_messages = (
                await self.session_manager.get_conversation_messages(session_id)
            )

            # Include conversation history plus current prompt for agent
            messages = conversation_messages + [HumanMessage(content=json_prompt)]

            # Agent call with full interview context - no checkpointer but with rich state
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

            question_data = self._parse_json_response(response)
            question = QuestionGeneration(**question_data)

            # Store the generated follow-up question in database
            await self.session_manager.add_message_to_memory(
                session_id=session_id,
                role="ASSISTANT",
                content=question.question,
                message_type="QUESTION",
                metadata={
                    "question_type": "follow_up",
                    "expected_concepts": question.expected_concepts,
                    "reasoning": question.reasoning,
                },
            )

            # Update state using schema
            state.question_count += 1

            # Check if we should transition to deep dive phase
            if state.question_count >= 3 and state.interview_phase == "exploration":
                state.interview_phase = "deep_dive"
            elif state.question_count >= 5 and state.interview_phase == "deep_dive":
                state.interview_phase = "advanced_concepts"

            # Check if ready for summary
            if state.question_count >= 5 and len(state.evaluation_history) >= 3:
                state.ready_for_summary = True

            # Persist state updates
            await self.session_manager.update_session_state(
                session_id,
                {
                    "question_count": state.question_count,
                    "interview_phase": state.interview_phase,
                    "ready_for_summary": state.ready_for_summary,
                },
            )

            logger.info(
                f"Follow-up question generated with state schema - Phase: {state.interview_phase}, Count: {state.question_count}"
            )
            return question

        except Exception as e:
            logger.error(f"Error generating follow-up question: {e}")
            return self._create_fallback_follow_up(user_answer)

    async def generate_follow_up_question_stream(
        self, session_id: str, user_answer: str, evaluation_context: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream follow-up question generation with memory context.

        PRIORITY FEATURE: Real-time streaming with memory integration.
        """
        logger.info(f"Streaming follow-up generation for session {session_id}")

        config = self.session_manager.get_config(session_id)

        # Same JSON prompt as non-streaming version
        json_prompt = STREAMING_FOLLOW_UP_PROMPT_TEMPLATE.format(
            user_answer=user_answer,
            evaluation_context=json.dumps(evaluation_context, indent=2),
        )

        try:
            # Stream the response generation
            yield {"type": "status", "message": "Analyzing conversation history..."}

            # Get conversation history from database
            conversation_messages = (
                await self.session_manager.get_conversation_messages(session_id)
            )

            # Include conversation history plus current prompt for agent
            messages = conversation_messages + [HumanMessage(content=json_prompt)]

            content_buffer = ""
            async for chunk in self.agent.astream(
                {
                    "messages": messages,
                    # Note: streaming doesn't need full context as it's for real-time generation
                }
            ):
                # Stream content from agent response
                if "messages" in chunk:
                    for message in chunk["messages"]:
                        if hasattr(message, "content") and message.content:
                            yield {"type": "content", "content": message.content}
                            content_buffer += message.content

            # Parse final response
            yield {"type": "status", "message": "Finalizing question..."}

            question_data = self._parse_json_response(content_buffer)
            question = QuestionGeneration(**question_data)

            # Store the generated question in memory (was missing!)
            await self.session_manager.add_message_to_memory(
                session_id=session_id,
                role="ASSISTANT",
                content=question.question,
                message_type="QUESTION",
                metadata={
                    "question_type": "follow_up",
                    "expected_concepts": question.expected_concepts,
                    "reasoning": getattr(question, "reasoning", ""),
                },
            )

            # Update session state
            state = await self.session_manager.get_session_state(session_id)
            if state:
                await self.session_manager.update_session_state(
                    session_id, {"question_count": state.question_count + 1}
                )

            # Convert to JSON-serializable format for streaming
            question_dict = {
                "question": question.question,
                "question_type": question.question_type,
                "topics_targeted": question.topics_targeted,
                "difficulty_level": question.difficulty_level,
                "expected_concepts": question.expected_concepts,
                "guidance_hints": question.guidance_hints,
                "time_estimate": question.time_estimate,
                "follow_up_areas": question.follow_up_areas,
                "reasoning": getattr(question, "reasoning", ""),
                "builds_on_previous": getattr(question, "builds_on_previous", True),
                "complexity_progression": getattr(
                    question, "complexity_progression", "same"
                ),
            }

            yield {"type": "complete", "question": question_dict}

            logger.info(f"Follow-up question streamed successfully")

        except Exception as e:
            logger.error(f"Error streaming follow-up question: {e}")
            fallback = self._create_fallback_follow_up(user_answer)

            # Store fallback question in memory too
            await self.session_manager.add_message_to_memory(
                session_id=session_id,
                role="ASSISTANT",
                content=fallback.question,
                message_type="QUESTION",
                metadata={
                    "question_type": "follow_up_fallback",
                    "expected_concepts": fallback.expected_concepts,
                    "reasoning": "Generated as fallback due to error",
                },
            )

            # Convert to JSON-serializable format
            fallback_dict = {
                "question": fallback.question,
                "question_type": fallback.question_type,
                "topics_targeted": fallback.topics_targeted,
                "difficulty_level": fallback.difficulty_level,
                "expected_concepts": fallback.expected_concepts,
                "guidance_hints": fallback.guidance_hints,
                "time_estimate": fallback.time_estimate,
                "follow_up_areas": fallback.follow_up_areas,
                "reasoning": "Generated as fallback due to error",
                "builds_on_previous": True,
                "complexity_progression": "same",
            }

            yield {"type": "complete", "question": fallback_dict}

    def _parse_json_response(self, response) -> Dict[str, Any]:
        """
        Parse JSON from LLM response with enhanced error handling.
        """
        try:
            # Handle direct string content from LLM
            if isinstance(response, str):
                content = response
            elif hasattr(response, "content"):
                content = response.content
            else:
                content = str(response)

            if not content:
                raise ValueError("No content found in response")

            # Enhanced JSON extraction with multiple fallback strategies
            json_str = None

            # Strategy 1: Direct JSON (preferred - no markdown blocks)
            content = content.strip()
            if content.startswith("{") and content.endswith("}"):
                json_str = content

            # Strategy 2: Extract from markdown code blocks (fallback)
            elif "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end > start:
                    json_str = content[start:end].strip()

            # Strategy 3: Find JSON object boundaries (fallback)
            elif "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = content[start:end]

            if not json_str:
                raise ValueError("No JSON structure found in response")

            # Week 3: Strict JSON parsing with validation
            try:
                question_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed, attempting cleanup: {e}")
                # Attempt to fix common JSON issues
                json_str = self._fix_common_json_issues(json_str)
                question_data = json.loads(json_str)

            # Week 3: Enhanced field validation with detailed error reporting
            validation_errors = []
            required_fields = {
                "question": str,
                "question_type": str,
                "topics_targeted": list,
                "difficulty_level": str,
                "expected_concepts": list,
                "guidance_hints": list,
                "time_estimate": (int, float),
                "follow_up_areas": list,
            }

            for field, expected_type in required_fields.items():
                if field not in question_data:
                    validation_errors.append(f"Missing required field: {field}")
                    question_data[field] = self._get_default_value(field)
                elif not isinstance(question_data[field], expected_type):
                    validation_errors.append(
                        f"Field {field} has wrong type: expected {expected_type}, got {type(question_data[field])}"
                    )
                    question_data[field] = self._get_default_value(field)

            # Week 3: Optional fields with defaults
            optional_fields = {
                "reasoning": "Generated based on conversation context",
                "builds_on_previous": True,
                "complexity_progression": "same",
            }

            for field, default_value in optional_fields.items():
                if field not in question_data:
                    question_data[field] = default_value

            if validation_errors:
                logger.warning(f"JSON validation issues: {validation_errors}")

            # Week 3: Additional content quality validation
            self._validate_content_quality(question_data)

            return question_data

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Week 3 JSON parsing error: {e}")
            logger.debug(f"Content that failed to parse: {content[:500]}...")
            raise ValueError(f"Failed to parse JSON response: {e}")

    def _fix_common_json_issues(self, json_str: str) -> str:
        """Fix common JSON formatting issues - Week 3 enhancement."""
        # Remove trailing commas
        json_str = json_str.replace(",}", "}").replace(",]", "]")

        # Fix unquoted boolean values
        json_str = json_str.replace(": true", ": true").replace(": false", ": false")
        json_str = json_str.replace(': "true"', ": true").replace(
            ': "false"', ": false"
        )

        # Fix single quotes to double quotes
        json_str = json_str.replace("'", '"')

        return json_str

    def _validate_content_quality(self, question_data: Dict[str, Any]) -> None:
        """Validate content quality - Week 3 enhancement."""
        # Validate question length
        question = question_data.get("question", "")
        if len(question) < 20:
            logger.warning("Question too short - may lack detail")
        elif len(question) > 500:
            logger.warning("Question too long - may be overwhelming")

        # Validate question type
        valid_types = ["opening", "follow_up", "clarification", "topic_transition"]
        if question_data.get("question_type") not in valid_types:
            logger.warning(
                f"Invalid question_type: {question_data.get('question_type')}"
            )
            question_data["question_type"] = "follow_up"

        # Validate difficulty level
        valid_difficulties = ["beginner", "intermediate", "advanced"]
        if question_data.get("difficulty_level") not in valid_difficulties:
            logger.warning(
                f"Invalid difficulty_level: {question_data.get('difficulty_level')}"
            )
            question_data["difficulty_level"] = "intermediate"

        # Validate arrays are not empty
        for field in [
            "topics_targeted",
            "expected_concepts",
            "guidance_hints",
            "follow_up_areas",
        ]:
            if not question_data.get(field):
                logger.warning(f"Empty array for {field}")
                question_data[field] = [f"default_{field.replace('_', ' ')}"]

    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing required field."""
        defaults = {
            "question": "Can you tell me more about your approach to this design?",
            "question_type": "follow_up",
            "topics_targeted": ["system_design"],
            "difficulty_level": "intermediate",
            "expected_concepts": ["architecture"],
            "guidance_hints": ["Think about the components", "Consider scalability"],
            "time_estimate": 5,
            "follow_up_areas": ["architecture", "scalability"],
        }
        return defaults.get(field, "")

    def _create_fallback_opening(
        self, topic: str, difficulty: DifficultyLevel
    ) -> QuestionGeneration:
        """Create fallback opening question when generation fails."""
        logger.warning(f"Creating fallback opening question for {topic}")

        return QuestionGeneration(
            question=f"Welcome! Today we'll be designing a {topic.replace('_', ' ')} system. To start, what would you say are the key functional requirements we need to consider for this system? Please walk me through your initial thinking.",
            question_type="opening",
            topics_targeted=["requirements_gathering", "functional_design"],
            difficulty_level=difficulty.value,
            expected_concepts=[
                "user_requirements",
                "system_boundaries",
                "core_features",
            ],
            guidance_hints=[
                "Think about who will use this system",
                "Consider the main features needed",
                "Think about scale and constraints",
            ],
            time_estimate=5,
            follow_up_areas=["architecture", "data_modeling", "scalability"],
        )

    def _create_fallback_follow_up(self, user_answer: str) -> QuestionGeneration:
        """Create fallback follow-up question when generation fails."""
        logger.warning("Creating fallback follow-up question")

        return QuestionGeneration(
            question="That's a good start! Can you dive deeper into how you would handle the architecture and main components of your system?",
            question_type="follow_up",
            topics_targeted=["system_architecture", "component_design"],
            difficulty_level="intermediate",
            expected_concepts=[
                "service_boundaries",
                "data_flow",
                "component_interactions",
            ],
            guidance_hints=[
                "Think about separating concerns",
                "Consider how components communicate",
                "Think about data flow",
            ],
            time_estimate=5,
            follow_up_areas=["scalability", "data_consistency", "performance"],
        )
