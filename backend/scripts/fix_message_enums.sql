-- Fix Message Enum Types to Match Python Code
-- This script fixes the mismatch between database enum values and Python enum values

BEGIN;

-- 1. First, let's see what we're working with
SELECT 'Current message_type enum values:' as info;
SELECT unnest(enum_range(NULL::message_type)) as current_values;

SELECT 'Current message_role enum values:' as info;
SELECT unnest(enum_range(NULL::message_role)) as current_values;

-- 2. Check if there's any existing data that needs conversion
SELECT 'Existing message roles in data:' as info;
SELECT DISTINCT role FROM messages WHERE role IS NOT NULL;

SELECT 'Existing message types in data:' as info;
SELECT DISTINCT message_type FROM messages WHERE message_type IS NOT NULL;

-- 3. Update existing data to uppercase before changing enum
UPDATE messages SET role = UPPER(role) WHERE role IS NOT NULL;
UPDATE messages SET message_type = UPPER(message_type) WHERE message_type IS NOT NULL;

-- 4. Handle any NULL values
UPDATE messages SET message_type = 'TEXT' WHERE message_type IS NULL;
UPDATE messages SET role = 'USER' WHERE role IS NULL;

-- 5. Change messages table to use text temporarily and remove any default
ALTER TABLE messages ALTER COLUMN role DROP DEFAULT;
ALTER TABLE messages ALTER COLUMN message_type DROP DEFAULT;
ALTER TABLE messages ALTER COLUMN role TYPE text;
ALTER TABLE messages ALTER COLUMN message_type TYPE text;

-- 6. Drop old enum types
DROP TYPE IF EXISTS message_role CASCADE;
DROP TYPE IF EXISTS message_type CASCADE;

-- 7. Create new enum types with uppercase values to match Python
CREATE TYPE message_role AS ENUM ('USER', 'ASSISTANT', 'SYSTEM');
CREATE TYPE message_type AS ENUM ('TEXT', 'QUESTION', 'ANSWER', 'FEEDBACK', 'CLARIFICATION', 'HINT');

-- 8. Convert table columns to use the new enum types
ALTER TABLE messages ALTER COLUMN role TYPE message_role USING role::message_role;
ALTER TABLE messages ALTER COLUMN message_type TYPE message_type USING message_type::message_type;

-- 9. Set default values (after the column is converted to enum type)
ALTER TABLE messages ALTER COLUMN message_type SET DEFAULT 'TEXT'::message_type;

-- 10. Make role NOT NULL if it isn't already
ALTER TABLE messages ALTER COLUMN role SET NOT NULL;

-- 11. Verify the changes
SELECT 'Updated message_type enum values:' as info;
SELECT unnest(enum_range(NULL::message_type)) as new_values;

SELECT 'Updated message_role enum values:' as info;
SELECT unnest(enum_range(NULL::message_role)) as new_values;

-- 12. Show table structure
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'messages' 
ORDER BY ordinal_position;

-- 13. Verify data after conversion
SELECT 'Data after conversion - roles:' as info;
SELECT DISTINCT role FROM messages;

SELECT 'Data after conversion - message types:' as info;
SELECT DISTINCT message_type FROM messages;

COMMIT;
