"""
Orchestrator Prompts
Specialized prompts for the Main Orchestrator Agent
"""

# Main orchestrator system prompts
ORCHESTRATOR_SYSTEM_PROMPTS = {
    "base": """
You are the Main Orchestrator for an AI-powered system design interview coaching platform.

Your role is to:
- Coordinate multiple specialized AI agents (Question Generator, Answer Evaluator, Feedback Provider, Difficulty Adaptor)
- Manage the conversation flow and interview state
- Determine the next best action based on context and evaluations
- Ensure educational objectives are met
- Maintain engaging and supportive interview experience

Key Principles:
- Always prioritize learning and skill development
- Adapt the interview flow based on candidate performance
- Ensure comprehensive topic coverage
- Maintain appropriate challenge level
- Provide clear reasoning for decisions

You must respond with structured JSON output following the exact schema provided.
""",
    "beginner": """
You are orchestrating a BEGINNER level system design interview.

BEGINNER Orchestration Guidelines:
- Provide more guidance and structure throughout
- Focus on conceptual understanding over optimization
- Allow more time for explanation and thinking
- Be encouraging and supportive in flow decisions
- Break complex topics into smaller, manageable parts
- Celebrate small wins and progress

Flow Decisions:
- Prefer clarification over moving forward when unclear
- Allow multiple attempts at explaining concepts
- Provide hints more liberally
- Transition topics when basic understanding is achieved

You must respond with structured JSON output following the exact schema provided.
""",
    "intermediate": """
You are orchestrating an INTERMEDIATE level system design interview.

INTERMEDIATE Orchestration Guidelines:
- Balance guidance with independent thinking
- Expect solid understanding of common patterns
- Focus on both concepts and implementation details
- Encourage trade-off discussions
- Cover multiple aspects of system design

Flow Decisions:
- Move forward when concepts are reasonably understood
- Push for deeper analysis when appropriate
- Introduce scalability considerations progressively
- Balance breadth and depth of coverage

You must respond with structured JSON output following the exact schema provided.
""",
    "advanced": """
You are orchestrating an ADVANCED level system design interview.

ADVANCED Orchestration Guidelines:
- Expect systematic and comprehensive approach
- Focus on production-ready solutions
- Challenge with complex constraints and edge cases
- Expect minimal guidance requirements
- Cover advanced topics like consistency, monitoring, optimization

Flow Decisions:
- Move quickly through basic concepts
- Focus heavily on optimization and trade-offs
- Expect discussion of failure scenarios
- Challenge assumptions and design choices

You must respond with structured JSON output following the exact schema provided.
""",
}

# Action determination prompts
ACTION_DETERMINATION_PROMPTS = {
    "next_action_analysis": """
Analyze the current interview state and determine the next best action:

CURRENT STATE:
- Session ID: {session_id}
- Topic: {topic}
- Difficulty: {difficulty}
- Current Phase: {current_phase}
- Questions Asked: {questions_asked}
- Average Performance: {average_performance}

LATEST INTERACTION:
- User Answer: {user_answer}
- Evaluation Results: {evaluation_results}
- Performance Trends: {performance_trends}

CONVERSATION CONTEXT:
- Topics Covered: {topics_covered}
- Gaps Identified: {gaps_identified}
- Time Elapsed: {time_elapsed}
- Engagement Level: {engagement_level}

ANALYSIS REQUIREMENTS:
Determine the most appropriate next action based on:

1. LEARNING PROGRESSION:
   - Is the candidate understanding the current topic?
   - Should we go deeper or move to next area?
   - Does anything need clarification?

2. PERFORMANCE ASSESSMENT:
   - How is the candidate performing overall?
   - Should difficulty be adjusted?
   - Are they ready for more challenge?

3. TOPIC COVERAGE:
   - What critical areas remain uncovered?
   - What's the logical next topic progression?
   - Have we achieved sufficient depth?

4. INTERVIEW FLOW:
   - How can we maintain engagement?
   - What would provide the best learning experience?
   - Should we provide feedback or continue questioning?

POSSIBLE ACTIONS:
- generate_follow_up: Continue with follow-up question on current topic
- generate_clarification: Ask for clarification of unclear areas  
- generate_topic_transition: Move to new topic area
- provide_feedback: Give detailed feedback on performance
- provide_hint: Offer guidance hint
- adjust_difficulty: Recommend difficulty level change
- generate_summary: Provide session summary (if near completion)

Response must include:
- recommended_action: The best next action
- reasoning: Why this action is recommended
- confidence_level: Confidence in recommendation (0-1)
- alternative_actions: Other viable options
- specific_context: Specific context for the action
""",
    "session_completion_analysis": """
Analyze if the interview session should be completed:

SESSION STATE:
- Duration: {duration_minutes} minutes
- Topics Covered: {topics_covered}
- Questions Asked: {question_count}
- Average Performance: {average_performance}
- Coverage Completeness: {coverage_percentage}%

COMPLETION CRITERIA:
Determine if session should be completed based on:

1. TIME FACTORS:
   - Has sufficient time been spent?
   - Are we approaching time limits?

2. COVERAGE FACTORS:
   - Have core topics been adequately covered?
   - Are there critical gaps remaining?

3. PERFORMANCE FACTORS:
   - Has the candidate demonstrated understanding?
   - Would continued discussion add value?

4. LEARNING FACTORS:
   - Has the candidate achieved learning objectives?
   - Would a summary be more valuable than continuing?

Response should indicate:
- should_complete: Boolean indicating if session should end
- completion_reason: Reason for completion/continuation
- recommended_next_steps: What should happen next
- session_summary_focus: Key areas to highlight in summary
""",
    "difficulty_adjustment_analysis": """
Analyze if difficulty should be adjusted:

PERFORMANCE DATA:
- Recent Scores: {recent_scores}
- Performance Trend: {performance_trend}
- Current Difficulty: {current_difficulty}
- Time in Current Difficulty: {time_in_difficulty}

ADJUSTMENT CRITERIA:
Consider adjustment based on:

1. PERFORMANCE PATTERNS:
   - Consistent high performance (8+ scores) → Increase difficulty
   - Consistent low performance (4- scores) → Decrease difficulty  
   - Fluctuating performance → Maintain current level

2. LEARNING INDICATORS:
   - Quick understanding → Ready for more challenge
   - Struggling with concepts → Need more support
   - Growing confidence → Can handle complexity

3. ENGAGEMENT FACTORS:
   - Seems bored → Increase challenge
   - Seems overwhelmed → Decrease challenge
   - Appropriately engaged → Maintain level

Response should include:
- should_adjust: Boolean indicating if adjustment needed
- recommended_difficulty: New difficulty level if adjusting
- adjustment_reasoning: Why adjustment is recommended
- transition_strategy: How to smoothly adjust difficulty
""",
}

# Interview phase definitions
INTERVIEW_PHASES = {
    "opening": {
        "description": "Initial requirements gathering and problem understanding",
        "typical_duration": "10-15 minutes",
        "key_objectives": [
            "Understand problem requirements",
            "Clarify scope and constraints",
            "Establish basic approach",
        ],
        "success_criteria": [
            "Clear problem understanding",
            "Reasonable initial approach",
            "Good communication",
        ],
    },
    "architecture": {
        "description": "High-level system design and component identification",
        "typical_duration": "15-20 minutes",
        "key_objectives": [
            "Define system components",
            "Establish component interactions",
            "Consider basic scalability",
        ],
        "success_criteria": [
            "Clear component design",
            "Logical data flow",
            "Scalability awareness",
        ],
    },
    "deep_dive": {
        "description": "Detailed exploration of critical components",
        "typical_duration": "15-25 minutes",
        "key_objectives": [
            "Detailed component design",
            "Technology choices and reasoning",
            "Trade-off discussions",
        ],
        "success_criteria": [
            "Technical depth",
            "Justified decisions",
            "Trade-off awareness",
        ],
    },
    "optimization": {
        "description": "Performance optimization and scaling discussions",
        "typical_duration": "10-15 minutes",
        "key_objectives": [
            "Bottleneck identification",
            "Optimization strategies",
            "Advanced scaling patterns",
        ],
        "success_criteria": [
            "Performance awareness",
            "Optimization strategies",
            "Advanced concepts",
        ],
    },
    "wrap_up": {
        "description": "Final questions, edge cases, and summary",
        "typical_duration": "5-10 minutes",
        "key_objectives": [
            "Address remaining gaps",
            "Discuss edge cases",
            "Provide comprehensive feedback",
        ],
        "success_criteria": [
            "Complete coverage",
            "Edge case awareness",
            "Clear learning outcomes",
        ],
    },
}

# Action priority matrix
ACTION_PRIORITY_MATRIX = {
    "high_priority": [
        "generate_clarification",  # When understanding is unclear
        "adjust_difficulty",  # When difficulty mismatch is significant
        "provide_hint",  # When candidate is clearly stuck
    ],
    "medium_priority": [
        "generate_follow_up",  # Normal flow progression
        "generate_topic_transition",  # Moving to new areas
        "provide_feedback",  # Performance feedback
    ],
    "low_priority": [
        "generate_summary",  # Only when session is complete
        "session_completion",  # End of interview
    ],
}

# Context weighting factors
CONTEXT_WEIGHTS = {
    "performance_trend": 0.3,  # How candidate is performing over time
    "topic_coverage": 0.25,  # How much has been covered
    "engagement_level": 0.2,  # How engaged the candidate seems
    "time_factors": 0.15,  # Time constraints and pacing
    "difficulty_match": 0.1,  # How well difficulty matches ability
}
