"""
AI Prompts for System Design Interview Agents
Centralized collection of prompts used by different AI agents
"""

# System Design Topics and Subtopics
SYSTEM_DESIGN_TOPICS = {
    "chat_system": {
        "name": "Chat System",
        "subtopics": [
            "Real-time messaging architecture",
            "Message delivery guarantees",
            "Presence and status tracking",
            "Group chat and channels",
            "Message history and search",
            "File sharing and media",
            "Scalability and sharding",
            "Security and encryption",
            "Mobile and web clients",
            "Push notifications",
        ],
        "key_concepts": [
            "WebSockets",
            "Message queues",
            "Database sharding",
            "Caching strategies",
            "Load balancing",
            "CDN",
            "Microservices",
            "Event-driven architecture",
        ],
    },
    "social_media_feed": {
        "name": "Social Media Feed",
        "subtopics": [
            "Feed generation algorithms",
            "Content ranking and scoring",
            "User timeline construction",
            "Real-time updates",
            "Content recommendation",
            "Image and video processing",
            "Social graph management",
            "Analytics and metrics",
            "Content moderation",
            "Advertising integration",
        ],
        "key_concepts": [
            "Graph databases",
            "Machine learning",
            "Content delivery",
            "Caching layers",
            "Message queues",
            "Data pipelines",
            "Real-time processing",
            "A/B testing",
        ],
    },
    "ride_sharing": {
        "name": "Ride Sharing System",
        "subtopics": [
            "Driver-rider matching algorithm",
            "Real-time location tracking",
            "Dynamic pricing model",
            "Route optimization",
            "Payment processing",
            "Trip lifecycle management",
            "Driver availability tracking",
            "Demand forecasting",
            "Fraud detection",
            "Customer support system",
        ],
        "key_concepts": [
            "Geospatial indexing",
            "Real-time tracking",
            "Graph algorithms",
            "Machine learning",
            "Payment gateways",
            "Event sourcing",
            "Microservices",
            "Data analytics",
        ],
    },
    "url_shortener": {
        "name": "URL Shortener",
        "subtopics": [
            "URL encoding strategies",
            "Database design and sharding",
            "Caching mechanisms",
            "Rate limiting",
            "Analytics and tracking",
            "Custom URL aliases",
            "Expiration and cleanup",
            "API design",
            "Security considerations",
            "High availability",
        ],
        "key_concepts": [
            "Base62 encoding",
            "Database sharding",
            "Redis caching",
            "Rate limiting",
            "Analytics pipelines",
            "CDN",
            "Load balancing",
            "Monitoring",
        ],
    },
    "search_engine": {
        "name": "Search Engine",
        "subtopics": [
            "Web crawling strategy",
            "Document indexing",
            "Query processing",
            "Ranking algorithms",
            "Distributed storage",
            "Real-time indexing",
            "Search suggestions",
            "Personalization",
            "Image and video search",
            "Performance optimization",
        ],
        "key_concepts": [
            "Inverted index",
            "TF-IDF",
            "PageRank",
            "Distributed systems",
            "MapReduce",
            "Elasticsearch",
            "Machine learning",
            "NLP",
            "Caching",
            "Load balancing",
        ],
    },
}

# Opening Question Templates
OPENING_QUESTION_PROMPTS = {
    "beginner": """
    Generate an opening question for a beginner-level system design interview.
    
    Guidelines:
    - Start with basic requirements gathering
    - Keep the scope manageable and focused
    - Encourage the candidate to think about users and basic functionality first
    - Avoid complex scalability requirements initially
    - Be encouraging and supportive in tone
    
    Example structure:
    1. Brief introduction to the problem
    2. Ask about basic requirements and assumptions
    3. Guide toward thinking about core functionality
    4. Provide context about what we're looking for
    """,
    "intermediate": """
    Generate an opening question for an intermediate-level system design interview.
    
    Guidelines:
    - Include both functional and non-functional requirements
    - Introduce scale considerations (users, requests, data)
    - Expect discussion of trade-offs
    - Include some specific constraints or requirements
    - Balance guidance with open-ended exploration
    
    Example structure:
    1. Problem statement with context
    2. Scale requirements and constraints
    3. Ask about approach to requirements gathering
    4. Hint at key areas to consider
    """,
    "advanced": """
    Generate an opening question for an advanced-level system design interview.
    
    Guidelines:
    - Present complex, realistic constraints
    - Include challenging scale requirements
    - Expect deep technical considerations
    - Include edge cases and failure scenarios
    - Minimal guidance, expect systematic approach
    
    Example structure:
    1. Complex problem statement
    2. Realistic scale and performance requirements
    3. Specific technical constraints
    4. Expect comprehensive solution approach
    """,
}

# Evaluation Criteria Prompts
EVALUATION_PROMPTS = {
    "clarity_assessment": """
    Evaluate the clarity and structure of the candidate's explanation:
    
    Excellent (9-10):
    - Crystal clear logical flow
    - Well-organized thoughts
    - Easy to follow reasoning
    - Appropriate level of detail
    
    Good (7-8):
    - Generally clear explanation
    - Minor organizational issues
    - Mostly easy to follow
    - Adequate detail level
    
    Fair (5-6):
    - Understandable but scattered
    - Some logical gaps
    - Requires clarification
    - Inconsistent detail level
    
    Poor (1-4):
    - Difficult to follow
    - Major logical issues
    - Unclear reasoning
    - Inappropriate detail level
    """,
    "technical_depth": """
    Evaluate the technical depth and accuracy of the response:
    
    Excellent (9-10):
    - Demonstrates deep understanding
    - Accurate technical details
    - Appropriate technology choices
    - Shows practical experience
    
    Good (7-8):
    - Solid technical understanding
    - Mostly accurate details
    - Reasonable technology choices
    - Some experience evident
    
    Fair (5-6):
    - Basic technical knowledge
    - Some technical gaps
    - Generic technology mentions
    - Limited practical insight
    
    Poor (1-4):
    - Limited technical understanding
    - Technical inaccuracies
    - Inappropriate technology choices
    - No practical insight
    """,
    "scalability_awareness": """
    Evaluate understanding of scalability and performance considerations:
    
    Excellent (9-10):
    - Comprehensive scalability discussion
    - Identifies key bottlenecks
    - Discusses growth patterns
    - Considers performance metrics
    
    Good (7-8):
    - Good scalability awareness
    - Identifies some bottlenecks
    - Mentions growth considerations
    - Basic performance understanding
    
    Fair (5-6):
    - Basic scalability concepts
    - Limited bottleneck identification
    - Minimal growth planning
    - Surface-level performance talk
    
    Poor (1-4):
    - Little scalability consideration
    - No bottleneck identification
    - No growth planning
    - No performance discussion
    """,
}

# Feedback Generation Prompts
FEEDBACK_PROMPTS = {
    "encouraging": """
    Provide encouraging feedback that:
    - Highlights what the candidate did well
    - Gently guides toward improvements
    - Builds confidence and engagement
    - Provides specific, actionable suggestions
    - Maintains a supportive, positive tone
    
    Structure:
    1. Positive acknowledgment
    2. Specific strengths identified  
    3. Gentle guidance for improvement
    4. Encouragement to continue
    """,
    "constructive": """
    Provide balanced constructive feedback that:
    - Acknowledges both strengths and areas for improvement
    - Provides specific examples and suggestions
    - Maintains a professional, helpful tone
    - Focuses on learning opportunities
    - Guides toward better approaches
    
    Structure:
    1. Acknowledge good points
    2. Identify specific improvement areas
    3. Provide concrete suggestions
    4. Set expectations for next steps
    """,
    "challenging": """
    Provide challenging feedback that:
    - Pushes for deeper thinking and higher standards
    - Identifies sophisticated improvement opportunities  
    - Expects more comprehensive solutions
    - Challenges assumptions and approaches
    - Maintains respect while being rigorous
    
    Structure:
    1. Acknowledge the attempt
    2. Identify areas needing deeper analysis
    3. Challenge to think more comprehensively
    4. Set higher expectations
    """,
    "final_comprehensive": """
    Provide comprehensive final feedback that:
    - Summarizes overall performance
    - Highlights key strengths and growth areas
    - Provides specific recommendations for improvement
    - Gives actionable next steps for learning
    - Ends with encouragement and support
    
    Include:
    - Performance summary
    - Technical understanding assessment
    - Communication skills evaluation
    - Areas of strength
    - Priority improvement areas
    - Specific learning recommendations
    - Next steps for preparation
    """,
}

# Difficulty Adjustment Prompts
DIFFICULTY_ADJUSTMENT_PROMPTS = {
    "increase_difficulty": """
    The candidate is performing well and may benefit from increased challenge.
    
    Consider increasing difficulty when:
    - Consistently high scores (8+) over multiple questions
    - Demonstrates deep technical knowledge
    - Proactively considers advanced topics
    - Shows confidence and clear thinking
    - Handles current level with ease
    
    Ways to increase difficulty:
    - Add more complex constraints
    - Introduce failure scenarios
    - Discuss advanced scalability patterns
    - Include edge cases and optimizations
    - Expect more detailed technical discussions
    """,
    "decrease_difficulty": """
    The candidate may be struggling and could benefit from reduced challenge.
    
    Consider decreasing difficulty when:
    - Consistently low scores (4-) over multiple questions
    - Shows confusion or lack of technical knowledge
    - Requires frequent clarification
    - Seems overwhelmed by current complexity
    - Making little progress on current topics
    
    Ways to decrease difficulty:
    - Simplify constraints and requirements
    - Provide more guidance and structure
    - Focus on basic concepts first
    - Break problems into smaller parts
    - Offer more hints and direction
    """,
    "maintain_difficulty": """
    The current difficulty level appears appropriate.
    
    Maintain difficulty when:
    - Scores in the 5-7 range consistently
    - Shows steady progress and learning
    - Handles current level with appropriate effort
    - Demonstrates engagement without overwhelm
    - Making reasonable progress through topics
    
    Continue with:
    - Current complexity level
    - Balanced guidance and independence
    - Steady progression through topics
    - Appropriate challenge level
    - Regular assessment of progress
    """,
}

# Question Type Templates
QUESTION_TYPE_TEMPLATES = {
    "clarification": """
    Generate a clarification question that:
    - Points out specific areas needing more detail
    - Guides the candidate toward better explanations
    - Maintains encouraging tone
    - Provides helpful context
    - Focuses on one or two key areas
    
    Example phrases:
    - "Could you elaborate on..."
    - "I'd like to understand better how..."
    - "Can you walk me through..."
    - "What considerations would you have for..."
    """,
    "follow_up": """
    Generate a follow-up question that:
    - Builds on the previous response
    - Digs deeper into the current topic
    - Tests understanding of implications
    - Explores related concepts
    - Maintains conversation flow
    
    Example structures:
    - "Given that approach, how would you handle..."
    - "What happens when..."
    - "How would this scale when..."
    - "What trade-offs do you see with..."
    """,
    "topic_transition": """
    Generate a topic transition that:
    - Acknowledges what's been covered
    - Smoothly moves to the next area
    - Explains why the new topic is important
    - Sets context for the discussion
    - Maintains interview momentum
    
    Example structures:
    - "Great work on [previous topic]. Now let's explore..."
    - "Building on what we've discussed, I'd like to dive into..."
    - "The next important area to consider is..."
    - "Now that we've covered [topic], how would you approach..."
    """,
    "progressive": """
    Generate a progressive question that:
    - Adds complexity to the current discussion
    - Introduces new constraints or requirements
    - Tests adaptability and deeper thinking
    - Builds toward a complete solution
    - Challenges current assumptions
    
    Example approaches:
    - Add scale constraints
    - Introduce failure scenarios  
    - Add new requirements
    - Consider edge cases
    - Optimize existing solutions
    """,
}

# Memory and Context Prompts
CONTEXT_ANALYSIS_PROMPTS = {
    "conversation_summary": """
    Analyze the conversation to provide:
    - Key topics discussed
    - Candidate's demonstrated strengths
    - Areas where they struggled
    - Overall progression pattern
    - Notable insights or approaches
    - Gaps in coverage
    """,
    "performance_trends": """
    Analyze performance trends to identify:
    - Improvement or decline patterns
    - Consistency in performance
    - Areas of consistent strength
    - Areas of ongoing challenge
    - Learning velocity
    - Engagement level changes
    """,
    "topic_coverage": """
    Analyze topic coverage to determine:
    - Completeness of coverage
    - Depth of discussion in each area
    - Areas needing more exploration
    - Natural progression opportunities
    - Missing critical components
    - Readiness for next topics
    """,
}
