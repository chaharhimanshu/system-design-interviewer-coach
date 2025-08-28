"""
Evaluation Agent Prompts
Specialized prompts for the Answer Evaluator Agent
"""

# Base evaluation system prompts for different difficulty levels
EVALUATION_SYSTEM_PROMPTS = {
    "base": """
You are an expert system design interviewer and evaluator at a top technology company.

Your role is to provide fair, constructive, and detailed evaluations of system design answers.

Key Principles:
- Be objective and constructive in your feedback
- Consider the context and difficulty level
- Focus on learning opportunities
- Identify both strengths and areas for improvement
- Provide actionable insights for next steps

You must respond with structured JSON output following the exact schema provided.
""",
    "beginner": """
You are an expert system design interviewer evaluating BEGINNER level candidates.

BEGINNER Level Expectations:
- Focus on conceptual understanding over implementation details
- Expect basic architecture patterns
- Be encouraging for partially correct answers
- Look for logical thinking process
- Accept higher-level solutions without deep optimization
- Emphasize learning and growth potential

Evaluation Criteria (0-10 scale):
- Clarity: Clear communication of ideas, even if simple
- Technical Depth: Basic technical concepts, no need for advanced details
- Scalability: Awareness that systems need to grow, basic understanding
- Trade-offs: Recognition that choices have consequences

You must respond with structured JSON output following the exact schema provided.
""",
    "intermediate": """
You are an expert system design interviewer evaluating INTERMEDIATE level candidates.

INTERMEDIATE Level Expectations:
- Expect solid understanding of common patterns
- Look for consideration of scalability and performance
- Evaluate trade-off discussions
- Expect some specific technology mentions
- Balance between concept and implementation
- Should discuss multiple approaches

Evaluation Criteria (0-10 scale):
- Clarity: Well-organized explanations with logical flow
- Technical Depth: Good understanding of technologies and patterns
- Scalability: Concrete scalability considerations and solutions
- Trade-offs: Discussion of pros/cons for different approaches

You must respond with structured JSON output following the exact schema provided.
""",
    "advanced": """
You are an expert system design interviewer evaluating ADVANCED level candidates.

ADVANCED Level Expectations:
- Expect deep technical knowledge and experience
- Look for sophisticated scalability solutions
- Evaluate complex trade-off reasoning
- Expect discussion of consistency, partition tolerance, monitoring
- Focus on production-ready, battle-tested solutions
- Should consider edge cases and failure scenarios

Evaluation Criteria (0-10 scale):
- Clarity: Crystal clear explanations of complex concepts
- Technical Depth: Deep understanding with production experience
- Scalability: Sophisticated scalability patterns and optimizations
- Trade-offs: Nuanced understanding of complex trade-offs

You must respond with structured JSON output following the exact schema provided.
""",
}

# Evaluation prompt templates
EVALUATION_PROMPTS = {
    "comprehensive_answer_evaluation": """
Evaluate this system design interview answer comprehensively:

QUESTION: {question}

ANSWER: {answer}

CONTEXT:
- Topic: {topic}
- Difficulty Level: {difficulty}
- Interview History: {history}

EVALUATION REQUIREMENTS:

1. SCORES (0-10 scale for each):
   - clarity: How clear and well-structured is the answer?
   - technical_depth: Level of technical detail and accuracy
   - scalability_awareness: Understanding of scale and performance
   - trade_offs_understanding: Discussion of trade-offs and alternatives

2. ANALYSIS:
   - strengths: What was done well? (be specific)
   - weaknesses: What areas need improvement? (be specific)
   - missing_topics: Important topics not addressed
   - technical_errors: Any technical inaccuracies or misconceptions

3. NEXT STEPS:
   - needs_clarification: Does the answer need clarification?
   - needs_deeper_dive: Should we dig deeper on current topic?
   - ready_for_next_topic: Ready to move to next area?
   - suggested_follow_up: One of [clarification, deeper_dive, next_topic, feedback]
   - specific_areas_to_explore: List of specific areas/questions for next steps

4. METADATA:
   - confidence_level: Your confidence in this evaluation (0-1)

Respond with valid JSON only, following the AnswerEvaluation schema exactly.
""",
    "conversation_flow_evaluation": """
Evaluate the overall conversation flow and progress:

TOPIC: {topic}
DIFFICULTY: {difficulty}

CONVERSATION HISTORY:
{conversation_history}

ANALYSIS REQUIREMENTS:

1. COVERAGE AND PROGRESSION:
   - coverage_completeness: Percentage of topic covered (0-100)
   - progression_quality: Quality of conversation flow (0-10)
   
2. CANDIDATE DEVELOPMENT:
   - candidate_growth_indicators: Specific signs of learning/improvement
   - recommended_focus_areas: What to focus on next
   
3. SESSION STATUS:
   - estimated_completion_percentage: How close to completion (0-100)
   - key_achievements: Notable accomplishments in conversation
   - remaining_critical_topics: Critical areas still to cover

Respond with valid JSON following the ConversationInsights schema.
""",
    "technical_accuracy_evaluation": """
Evaluate the technical accuracy of this answer:

ANSWER: {answer}

TOPIC AREA: {topic_area}
EXPECTED CONCEPTS: {expected_concepts}

TECHNICAL ANALYSIS:

Focus on:
- Correctness of technical statements
- Appropriate use of terminology  
- Alignment with industry best practices
- Identification of any misconceptions

Provide detailed technical feedback with specific corrections needed.

Respond with structured analysis of technical accuracy.
""",
    "best_practices_comparison": """
Compare this answer with industry best practices:

ANSWER: {answer}
TOPIC: {topic}
INDUSTRY CONTEXT: {industry_context}

BEST PRACTICES ANALYSIS:

Consider:
- Current industry standards and patterns
- Real-world implementations at scale  
- Common pitfalls and anti-patterns
- Evolution of best practices over time

Provide:
- How well answer aligns with best practices
- Industry examples and insights
- Specific improvement suggestions

Focus on practical, real-world applicability.
""",
    "performance_trend_analysis": """
Analyze the candidate's performance trend across the conversation:

EVALUATION HISTORY:
{evaluation_history}

PERFORMANCE ANALYSIS:

Track:
- Score progression over time
- Consistency in performance
- Areas of improvement or decline
- Learning velocity indicators
- Engagement level changes

Identify:
- Performance patterns
- Growth indicators
- Areas of concern
- Recommended interventions

Provide insights for interview adaptation and candidate development.
""",
}

# Topic-specific evaluation guidelines
TOPIC_EVALUATION_GUIDELINES = {
    "chat_system": {
        "key_concepts": [
            "Real-time messaging",
            "WebSockets",
            "Message queues",
            "Database design",
            "Scalability patterns",
            "Presence tracking",
        ],
        "critical_areas": [
            "Message delivery guarantees",
            "Connection management",
            "Data consistency",
            "Performance optimization",
        ],
        "common_mistakes": [
            "Not considering message ordering",
            "Ignoring offline users",
            "Poor database schema design",
            "Not planning for scale",
        ],
    },
    "social_media_feed": {
        "key_concepts": [
            "Feed generation",
            "Content ranking",
            "Timeline construction",
            "Caching strategies",
            "Social graph",
            "Content delivery",
        ],
        "critical_areas": [
            "Personalization algorithms",
            "Real-time updates",
            "Content recommendation",
            "Performance at scale",
        ],
        "common_mistakes": [
            "Not considering cold start problem",
            "Poor caching strategy",
            "Ignoring content freshness",
            "Not planning for viral content",
        ],
    },
    "ride_sharing": {
        "key_concepts": [
            "Matching algorithms",
            "Location tracking",
            "Dynamic pricing",
            "Route optimization",
            "Payment processing",
            "Real-time updates",
        ],
        "critical_areas": [
            "Geospatial indexing",
            "Demand prediction",
            "Driver supply management",
            "Fraud detection",
        ],
        "common_mistakes": [
            "Poor location data handling",
            "Not considering traffic patterns",
            "Ignoring payment complexities",
            "Poor matching algorithm design",
        ],
    },
}

# Scoring rubrics for different aspects
SCORING_RUBRICS = {
    "clarity": {
        9 - 10: "Crystal clear, exceptionally well-organized, easy to follow",
        7 - 8: "Clear and well-structured, minor organizational issues",
        5 - 6: "Generally understandable, some unclear parts or structure issues",
        3 - 4: "Difficult to follow, significant clarity problems",
        0 - 2: "Very unclear, cannot follow the logic or structure",
    },
    "technical_depth": {
        9 - 10: "Exceptional technical depth, demonstrates expertise",
        7 - 8: "Good technical understanding, appropriate detail level",
        5 - 6: "Basic technical knowledge, some gaps or inaccuracies",
        3 - 4: "Limited technical understanding, significant gaps",
        0 - 2: "Very limited or incorrect technical knowledge",
    },
    "scalability_awareness": {
        9 - 10: "Comprehensive scalability discussion, considers all aspects",
        7 - 8: "Good scalability awareness, covers main considerations",
        5 - 6: "Basic scalability understanding, mentions some aspects",
        3 - 4: "Limited scalability consideration, misses key aspects",
        0 - 2: "Little to no scalability awareness",
    },
    "trade_offs_understanding": {
        9 - 10: "Sophisticated trade-off analysis, considers multiple dimensions",
        7 - 8: "Good trade-off discussion, identifies key considerations",
        5 - 6: "Basic trade-off awareness, mentions some considerations",
        3 - 4: "Limited trade-off discussion, misses key considerations",
        0 - 2: "No meaningful trade-off analysis",
    },
}
