-- Migration script to add missing columns to sessions table
-- This adds the columns that are in SessionModel but missing from the database

-- Add the missing columns to sessions table
DO $$
BEGIN
    -- Add max_duration_minutes if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'sessions' AND column_name = 'max_duration_minutes'
    ) THEN
        ALTER TABLE sessions ADD COLUMN max_duration_minutes INTEGER NOT NULL DEFAULT 60;
    END IF;

    -- Add enable_hints if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'sessions' AND column_name = 'enable_hints'
    ) THEN
        ALTER TABLE sessions ADD COLUMN enable_hints BOOLEAN NOT NULL DEFAULT TRUE;
    END IF;

    -- Add enable_real_time_feedback if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'sessions' AND column_name = 'enable_real_time_feedback'
    ) THEN
        ALTER TABLE sessions ADD COLUMN enable_real_time_feedback BOOLEAN NOT NULL DEFAULT TRUE;
    END IF;

    -- Add custom_requirements if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'sessions' AND column_name = 'custom_requirements'
    ) THEN
        ALTER TABLE sessions ADD COLUMN custom_requirements TEXT;
    END IF;

    -- Add session_config if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'sessions' AND column_name = 'session_config'
    ) THEN
        ALTER TABLE sessions ADD COLUMN session_config JSONB DEFAULT '{}';
    END IF;

    -- Add created_at if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'sessions' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE sessions ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
    END IF;

    -- Add updated_at if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'sessions' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE sessions ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
    END IF;

    -- Note: The database already uses custom enum types for status and difficulty_level
    -- No need to add CHECK constraints as the enum types already enforce valid values

END$$;

-- Ensure messages table has the correct structure
DO $$
BEGIN
    -- Add tokens_used if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'messages' AND column_name = 'tokens_used'
    ) THEN
        ALTER TABLE messages ADD COLUMN tokens_used INTEGER NOT NULL DEFAULT 0;
    END IF;

    -- Rename metadata to message_metadata if needed
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'messages' AND column_name = 'metadata'
    ) THEN
        ALTER TABLE messages RENAME COLUMN metadata TO message_metadata;
    END IF;
    
    -- Add message_metadata if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'messages' AND column_name = 'message_metadata'
    ) THEN
        ALTER TABLE messages ADD COLUMN message_metadata JSONB DEFAULT '{}';
    END IF;
END$$;

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_topic ON sessions(topic);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);

-- Display current table structure for verification
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'sessions' 
ORDER BY ordinal_position;
