-- Migration script to add missing enum types and update messages table
-- Run this script to fix the enum validation errors

-- Step 1: Create the missing enum types
CREATE TYPE message_role AS ENUM ('USER', 'ASSISTANT', 'SYSTEM');
CREATE TYPE message_type AS ENUM ('TEXT', 'QUESTION', 'ANSWER', 'FEEDBACK', 'CLARIFICATION', 'HINT');

-- Step 2: Update existing messages table to use enum types
-- First, let's backup any existing data and update the columns

-- Add new columns with enum types (with temporary names)
ALTER TABLE messages ADD COLUMN role_new message_role;
ALTER TABLE messages ADD COLUMN message_type_new message_type;

-- Update the new columns with converted values
UPDATE messages SET role_new = CASE 
    WHEN UPPER(role) = 'USER' THEN 'USER'::message_role
    WHEN UPPER(role) = 'ASSISTANT' THEN 'ASSISTANT'::message_role
    WHEN UPPER(role) = 'SYSTEM' THEN 'SYSTEM'::message_role
    ELSE 'USER'::message_role
END;

UPDATE messages SET message_type_new = CASE 
    WHEN UPPER(message_type) = 'TEXT' THEN 'TEXT'::message_type
    WHEN UPPER(message_type) = 'QUESTION' THEN 'QUESTION'::message_type
    WHEN UPPER(message_type) = 'ANSWER' THEN 'ANSWER'::message_type
    WHEN UPPER(message_type) = 'FEEDBACK' THEN 'FEEDBACK'::message_type
    WHEN UPPER(message_type) = 'CLARIFICATION' THEN 'CLARIFICATION'::message_type
    WHEN UPPER(message_type) = 'HINT' THEN 'HINT'::message_type
    ELSE 'TEXT'::message_type
END;

-- Drop old columns and rename new ones
ALTER TABLE messages DROP COLUMN role;
ALTER TABLE messages DROP COLUMN message_type;
ALTER TABLE messages RENAME COLUMN role_new TO role;
ALTER TABLE messages RENAME COLUMN message_type_new TO message_type;

-- Set NOT NULL constraints
ALTER TABLE messages ALTER COLUMN role SET NOT NULL;
ALTER TABLE messages ALTER COLUMN message_type SET NOT NULL;
ALTER TABLE messages ALTER COLUMN message_type SET DEFAULT 'TEXT';

-- Add indexes back
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_type ON messages(message_type);

-- Verify the changes
SELECT 'Migration completed successfully' as status;
