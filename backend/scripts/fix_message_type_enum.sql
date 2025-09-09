-- Fix message_type enum to match domain entities
-- Add missing enum values that exist in code but not in database

-- Add missing values to message_type enum
ALTER TYPE message_type ADD VALUE IF NOT EXISTS 'ANSWER';
ALTER TYPE message_type ADD VALUE IF NOT EXISTS 'CLARIFICATION';
ALTER TYPE message_type ADD VALUE IF NOT EXISTS 'HINT';

-- Also make sure we have all the values from the domain
-- The database already has: TEXT, CODE, DIAGRAM, FEEDBACK, QUESTION, EVALUATION
-- We're adding: ANSWER, CLARIFICATION, HINT

-- Display current enum values for verification
SELECT 
    t.typname AS enum_name,
    array_agg(e.enumlabel ORDER BY e.enumsortorder) AS enum_values
FROM pg_type t 
JOIN pg_enum e ON t.oid = e.enumtypid  
WHERE t.typname = 'message_type'
GROUP BY t.typname;
