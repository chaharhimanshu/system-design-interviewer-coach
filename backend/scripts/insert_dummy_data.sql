-- ============================================================================
-- INSERT SAMPLE DATA
-- ============================================================================

-- Insert default interview tools
INSERT INTO interview_tools (id, name, description) VALUES
    (gen_random_uuid(), 'System Design', "Design and visualize scalable software architectures with ease"),
    (gen_random_uuid(), 'Coding Interview', 'Conduct real-time coding interviews with live collaboration and evaluation'),
    (gen_random_uuid(), 'Behavioral Interview', 'Assess soft skills with structured questions and consistent evaluation'),
    (gen_random_uuid(), 'Product Design', 'Evaluate product thinking and design strategy through interactive sessions')
ON CONFLICT DO NOTHING;

-- Insert default subscription tiers
INSERT INTO subscriptions (tier, details, pricing) VALUES
    ('free', 'Free tier with limited interviews', 0.00),
    ('premium', 'Premium tier with unlimited interviews', 999.00),
    ('enterprise', 'Enterprise tier with advanced features', 2999.00)
ON CONFLICT DO NOTHING;

-- Insert default system topics
WITH tool_ids AS (
    SELECT id FROM interview_tools WHERE name = 'System Design' LIMIT 1
)
INSERT INTO topics (tool_id, topic_name, type, topic_description, level) 
SELECT 
    tool_ids.id,
    topic_data.name,
    'system',
    topic_data.description,
    topic_data.level::topic_level
FROM tool_ids,
(VALUES 
    -- Twitter/X
    ('Twitter/X', 'Design a basic feed system for a social media platform', 'beginner'),
    ('Twitter/X', 'Design a scalable social media feed with user timelines and followers', 'intermediate'),
    ('Twitter/X', 'Design Twitter at scale with timelines, trends, notifications, and high availability', 'advanced'),

    -- Netflix
    ('Netflix', 'Design a simple video streaming app with basic playback features', 'beginner'),
    ('Netflix', 'Design a streaming platform with content delivery and user profiles', 'intermediate'),
    ('Netflix', 'Design Netflix at scale with adaptive bitrate streaming and recommendation engines', 'advanced'),

    -- Uber
    ('Uber', 'Design a basic ride booking system with location input', 'beginner'),
    ('Uber', 'Design a ride-sharing system with driver and rider matching', 'intermediate'),
    ('Uber', 'Design Uber at scale with real-time location tracking and dynamic pricing', 'advanced'),

    -- Instagram
    ('Instagram', 'Design a photo sharing feature with user profiles', 'beginner'),
    ('Instagram', 'Design a media sharing app with feed, likes, and comments', 'intermediate'),
    ('Instagram', 'Design Instagram at scale with stories, explore, and content delivery optimization', 'advanced'),

    -- WhatsApp
    ('WhatsApp', 'Design a simple one-to-one messaging system', 'beginner'),
    ('WhatsApp', 'Design a chat system with message delivery and presence updates', 'intermediate'),
    ('WhatsApp', 'Design WhatsApp at scale with end-to-end encryption and group messaging', 'advanced'),

    -- YouTube
    ('YouTube', 'Design a video upload and playback system', 'beginner'),
    ('YouTube', 'Design a video platform with streaming, likes, and comments', 'intermediate'),
    ('YouTube', 'Design YouTube at scale with search, recommendations, and content distribution', 'advanced'),

    -- Custom Topic
    ('Custom Topic', 'Create your own system design problem tailored to your interview needs.','beginner')
) AS topic_data(name, description, level)
ON CONFLICT DO NOTHING;


WITH tool_ids AS (
    SELECT id FROM interview_tools WHERE name = 'Behavioral Interview' LIMIT 1
)
INSERT INTO topics (tool_id, topic_name, type, topic_description, level)
SELECT 
    tool_ids.id,
    topic_data.name,
    'system',
    topic_data.description,
    topic_data.level::topic_level
FROM tool_ids,
(VALUES
    ('Leadership', 'Evaluate a candidate’s ability to lead, influence, and motivate others.','intermediate'),
    ('Conflict Resolution', 'Assess how the candidate handles disagreements and difficult interpersonal situations.','intermediate'),
    ('Project Management', 'Understand the candidate’s approach to planning, executing, and managing projects.','intermediate'),
    ('Team Collaboration', 'Gauge the ability to work effectively and respectfully with diverse teams.','intermediate'),
    ('Problem Solving', 'Evaluate critical thinking and decision-making in challenging situations.','intermediate'),
    ('Custom Question', 'Create your own behavioral question tailored to your interview needs.','intermediate')
) AS topic_data(name, description, level)
ON CONFLICT DO NOTHING;


WITH tool_ids AS (
    SELECT id FROM interview_tools WHERE name = 'Coding Interview' LIMIT 1
)
INSERT INTO topics (tool_id, topic_name, type, topic_description, level)
SELECT 
    tool_ids.id,
    topic_data.name,
    'system',
    topic_data.description,
    topic_data.level::topic_level
FROM tool_ids,
(VALUES
    ('Arrays & Strings', 'Assess skills in manipulating arrays and strings efficiently.','intermediate'),
    ('Recursion & Backtracking', 'Evaluate understanding of recursive problem solving and state-space traversal.','intermediate'),
    ('Sorting & Searching', 'Test algorithmic knowledge in sorting techniques and binary search strategies.','intermediate'),
    ('Linked Lists', 'Assess ability to work with singly and doubly linked list operations.','intermediate'),
    ('Dynamic Programming', 'Evaluate the ability to optimize recursive problems using memoization or tabulation.','intermediate'),
    ('Trees & Graphs', 'Test traversal, search, and manipulation of tree and graph data structures.','intermediate'),
    ('Custom Question', 'Create your own coding problem tailored to your interview needs.','intermediate')
) AS topic_data(name, description, level)
ON CONFLICT DO NOTHING;


WITH tool_ids AS (
    SELECT id FROM interview_tools WHERE name = 'Product Design' LIMIT 1
)
INSERT INTO topics (tool_id, topic_name, type, topic_description, level)
SELECT 
    tool_ids.id,
    topic_data.name,
    'system',
    topic_data.description,
    topic_data.level::topic_level
FROM tool_ids,
(VALUES
    ('Mobile App', 'Design a mobile-first product experience focused on usability and responsiveness.','intermediate'),
    ('Web Platform', 'Design a scalable and accessible web-based platform with core functionality.','intermediate'),
    ('Feature Design', 'Evaluate how a candidate approaches the design of a specific product feature.','intermediate'),
    ('User Research', 'Assess understanding of gathering user insights and applying them to design decisions.','intermediate'),
    ('Custom Product', 'Create your own product design problem tailored to your interview objectives.','beginner')
) AS topic_data(name, description, level)
ON CONFLICT DO NOTHING;