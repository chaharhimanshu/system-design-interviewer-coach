"""
Question Generation Prompts
Specialized prompts for the Question Generator Agent
"""

# Question generation system prompts
QUESTION_GENERATION_SYSTEM_PROMPTS = {
    "base": """
You are an expert system design interviewer at a top technology company.

Your role is to generate intelligent, contextual questions that:
- Guide candidates through system design discussions
- Adapt to their skill level and responses
- Cover all critical aspects of the topic
- Maintain engaging conversation flow
- Provide appropriate challenge without overwhelm

You must respond with structured JSON output following the exact schema provided.
""",
    "beginner": """
You are generating questions for BEGINNER level system design candidates.

BEGINNER Question Guidelines:
- Start with basic requirements gathering
- Use encouraging, supportive language
- Break complex topics into smaller parts
- Provide more guidance and structure
- Focus on conceptual understanding
- Ask about user needs and basic functionality first
- Avoid overwhelming technical details initially

Question Characteristics:
- Clear and straightforward language
- Step-by-step approach
- Hints about what to consider
- Encouraging tone
- Building blocks approach

You must respond with structured JSON output following the exact schema provided.
""",
    "intermediate": """
You are generating questions for INTERMEDIATE level system design candidates.

INTERMEDIATE Question Guidelines:
- Balance guidance with independence
- Include both functional and non-functional requirements
- Introduce scale considerations
- Expect discussion of trade-offs
- Cover technology choices and reasoning
- Ask about specific design decisions

Question Characteristics:
- Moderate complexity
- Some guidance with room for exploration
- Technical depth appropriate to level
- Trade-off discussions
- Real-world constraints

You must respond with structured JSON output following the exact schema provided.
""",
    "advanced": """
You are generating questions for ADVANCED level system design candidates.

ADVANCED Question Guidelines:
- Minimal guidance, expect systematic approach
- Complex, realistic constraints
- Edge cases and failure scenarios
- Deep technical considerations
- Production-level concerns
- Optimization and efficiency discussions

Question Characteristics:
- High complexity and sophistication
- Minimal hand-holding
- Production system concerns
- Advanced technical concepts
- Multiple constraint considerations

You must respond with structured JSON output following the exact schema provided.
""",
}

# Question type-specific prompts
QUESTION_TYPE_PROMPTS = {
    "opening_question": """
Generate an opening question for a system design interview:

REQUIREMENTS:
- Topic: {topic}
- Difficulty Level: {difficulty}
- Context: {context}

OPENING QUESTION GUIDELINES:
1. Set the stage for the interview
2. Introduce the problem clearly
3. Provide appropriate context
4. Guide toward requirements gathering
5. Set expectations for discussion depth

Consider:
- Problem statement clarity
- Scope definition
- Initial guidance level
- Engagement factor
- Learning objectives

Generate a question that will start an engaging, educational discussion.

Response must include:
- question: The actual interview question
- question_type: "opening"
- topics_targeted: List of topics this question aims to explore
- difficulty_level: The difficulty level
- expected_concepts: Concepts candidate should ideally discuss
- guidance_hints: Hints available if candidate struggles
""",
    "follow_up_question": """
Generate a follow-up question based on the conversation:

CONTEXT:
- Previous Question: {previous_question}
- User Answer: {user_answer}
- Topic: {topic}
- Difficulty: {difficulty}
- Evaluation: {evaluation}

FOLLOW-UP GUIDELINES:
1. Build on the previous response
2. Dig deeper into current topic or transition
3. Address gaps identified in evaluation
4. Maintain conversation momentum
5. Progressive complexity

Based on the evaluation:
- Strengths to build upon: {strengths}
- Weaknesses to address: {weaknesses}
- Missing topics: {missing_topics}
- Suggested follow-up: {suggested_follow_up}

Generate a contextual follow-up question that advances the discussion.

Response must include:
- question: The follow-up question
- question_type: "follow_up"
- topics_targeted: Topics this question explores
- difficulty_level: Current difficulty level
- expected_concepts: Concepts to be discussed
- guidance_hints: Available hints for guidance
""",
    "clarification_question": """
Generate a clarification question to address unclear areas:

CONTEXT:
- Current Topic: {topic}
- User's Previous Answer: {answer}
- Areas Needing Clarification: {unclear_areas}
- Difficulty Level: {difficulty}

CLARIFICATION GUIDELINES:
1. Point out specific areas needing more detail
2. Guide toward better explanations
3. Maintain encouraging tone
4. Provide helpful context
5. Focus on 1-2 key areas

Generate a question that helps clarify the unclear areas while maintaining interview flow.

Response must include:
- question: The clarification question
- question_type: "clarification"
- topics_targeted: Specific areas to clarify
- difficulty_level: Current difficulty level
- expected_concepts: What should be clarified
- guidance_hints: Helpful hints for clarification
""",
    "topic_transition": """
Generate a topic transition question:

CONTEXT:
- Current Topic Covered: {current_topic}
- Next Topic: {next_topic}
- Progress So Far: {progress}
- Difficulty Level: {difficulty}

TRANSITION GUIDELINES:
1. Acknowledge what's been covered
2. Smoothly introduce the next area
3. Explain why the new topic is important
4. Set context for the discussion
5. Maintain interview momentum

Generate a smooth transition that connects the topics logically.

Response must include:
- question: The transition question
- question_type: "topic_transition"
- topics_targeted: New topics being introduced
- difficulty_level: Current difficulty level
- expected_concepts: Concepts for new topic
- guidance_hints: Guidance for the new area
""",
}

# Topic-specific question templates
TOPIC_QUESTION_TEMPLATES = {
    "chat_system": {
        "opening": {
            "beginner": "Let's design a simple chat application like WhatsApp. Start by telling me what you think the basic requirements would be. What should users be able to do?",
            "intermediate": "Design a real-time chat system that can handle millions of users. What are the key functional and non-functional requirements you'd consider?",
            "advanced": "Design a globally distributed chat system like Discord that handles 150 million active users with sub-second message delivery. Consider the full architecture including edge cases.",
        },
        "key_areas": [
            "Real-time messaging",
            "User presence",
            "Message delivery",
            "Scalability",
            "Data storage",
            "Security",
            "Mobile support",
        ],
    },
    "social_media_feed": {
        "opening": {
            "beginner": "Let's build a social media feed like Instagram. What basic features should it have and how would users interact with it?",
            "intermediate": "Design a social media feed system for 100 million users. How would you handle post creation, feed generation, and content delivery?",
            "advanced": "Design Facebook's news feed system with personalized content ranking, real-time updates, and global scale. Include content recommendation algorithms.",
        },
        "key_areas": [
            "Content creation",
            "Feed generation",
            "Personalization",
            "Real-time updates",
            "Content recommendation",
            "Scalability",
        ],
    },
    "ride_sharing": {
        "opening": {
            "beginner": "Let's design a ride-sharing app like Uber. What are the main features users (both riders and drivers) would need?",
            "intermediate": "Design a ride-sharing system for a major city. How would you handle driver-rider matching, real-time tracking, and payments?",
            "advanced": "Design Uber's backend system handling 15 million rides per day globally. Include dynamic pricing, fraud detection, and supply-demand optimization.",
        },
        "key_areas": [
            "Driver-rider matching",
            "Real-time tracking",
            "Payments",
            "Dynamic pricing",
            "Route optimization",
            "Supply management",
        ],
    },
}

# Progressive questioning strategies
PROGRESSIVE_STRATEGIES = {
    "requirements_to_design": """
Transition from requirements gathering to high-level design:
- "Now that we understand the requirements, how would you approach the high-level architecture?"
- "What would be the main components of your system?"
- "How would these components interact with each other?"
""",
    "design_to_scale": """
Transition from basic design to scalability:
- "How would your design handle 10x the current load?"
- "What bottlenecks do you see in your current design?"
- "How would you scale each component independently?"
""",
    "scale_to_details": """
Transition from scaling to detailed design:
- "Let's dive deeper into [specific component]. How would you implement this?"
- "What specific technologies would you choose and why?"
- "How would you handle edge cases in this component?"
""",
    "details_to_tradeoffs": """
Transition to trade-off discussions:
- "What are the trade-offs of this approach?"
- "How would you choose between [option A] and [option B]?"
- "What would you optimize for in this design?"
""",
}

# Question complexity modifiers
COMPLEXITY_MODIFIERS = {
    "increase_complexity": [
        "Add failure scenarios and how to handle them",
        "Consider global scale and multiple data centers",
        "Include advanced features like machine learning",
        "Discuss consistency and partition tolerance",
        "Add monitoring and observability requirements",
    ],
    "decrease_complexity": [
        "Focus on core functionality first",
        "Simplify to single data center deployment",
        "Use managed services where possible",
        "Defer advanced features for later",
        "Concentrate on happy path scenarios",
    ],
    "maintain_complexity": [
        "Continue with current level of detail",
        "Explore the current topic more thoroughly",
        "Ask for reasoning behind design choices",
        "Discuss alternative approaches",
        "Validate understanding with examples",
    ],
}

# Hint generation templates
HINT_TEMPLATES = {
    "conceptual": "Think about {concept} - this is often used in {context} to solve {problem}",
    "technical": "Consider using {technology} for this use case because it provides {benefits}",
    "approach": "A common approach here is to {approach} which helps with {advantages}",
    "example": "For example, {example_company} handles this by {solution} which addresses {concerns}",
}
