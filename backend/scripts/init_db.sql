-- Database Schema for System Design Interview Coach
-- Run this script to initialize your PostgreSQL database

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create ENUM types
DO $$ BEGIN
    CREATE TYPE user_status AS ENUM ('ACTIVE', 'INACTIVE', 'SUSPENDED', 'DELETED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('USER', 'ADMIN', 'MODERATOR');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE difficulty_level AS ENUM ('BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE session_status AS ENUM ('ACTIVE', 'COMPLETED', 'ABANDONED', 'PAUSED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE message_role AS ENUM ('USER', 'SYSTEM', 'ASSISTANT');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE message_type AS ENUM ('TEXT', 'CODE', 'DIAGRAM', 'FEEDBACK', 'QUESTION', 'EVALUATION');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    google_id VARCHAR(255) NOT NULL UNIQUE,
    status user_status NOT NULL DEFAULT 'ACTIVE',
    role user_role NOT NULL DEFAULT 'USER',
    
    -- Profile fields (some may be encrypted in application layer)
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone_number_encrypted TEXT,
    company VARCHAR(100),
    job_title VARCHAR(100),
    years_of_experience INTEGER,
    bio TEXT,
    avatar_url VARCHAR(500),
    
    -- JSON fields for complex data
    preferences JSONB NOT NULL DEFAULT '{}',
    subscription_data JSONB NOT NULL DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMPTZ,
    
    -- Verification and compliance
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    terms_accepted_at TIMESTAMPTZ,
    privacy_accepted_at TIMESTAMPTZ
);

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Session configuration
    topic VARCHAR(200) NOT NULL,
    difficulty_level difficulty_level NOT NULL DEFAULT 'INTERMEDIATE',
    max_duration_minutes INTEGER NOT NULL DEFAULT 60,
    enable_hints BOOLEAN NOT NULL DEFAULT TRUE,
    enable_real_time_feedback BOOLEAN NOT NULL DEFAULT TRUE,
    custom_requirements TEXT,
    
    -- Session status and timing
    status session_status NOT NULL DEFAULT 'ACTIVE',
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMPTZ,
    total_duration INTEGER, -- in seconds
    
    -- Session metadata
    session_config JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- Message content and metadata
    role message_role NOT NULL,
    content TEXT NOT NULL,
    message_type message_type NOT NULL DEFAULT 'TEXT',
    
    -- Message timing and usage
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tokens_used INTEGER NOT NULL DEFAULT 0,
    
    -- Flexible metadata storage
    message_metadata JSONB NOT NULL DEFAULT '{}'
);

-- Create indexes for performance
-- User indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_email_status ON users(email, status);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_subscription_data ON users USING GIN(subscription_data);

-- Session indexes
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_user_status ON sessions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_sessions_topic ON sessions(topic);
CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON sessions(started_at);
CREATE INDEX IF NOT EXISTS idx_sessions_difficulty ON sessions(difficulty_level);

-- Message indexes
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_session_timestamp ON messages(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type);

-- Create trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic updated_at
DROP TRIGGER IF EXISTS trigger_users_updated_at ON users;
CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_sessions_updated_at ON sessions;
CREATE TRIGGER trigger_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE users IS 'User accounts with authentication and profile information';
COMMENT ON TABLE sessions IS 'Interview sessions with configuration and status tracking';
COMMENT ON TABLE messages IS 'Conversation messages within interview sessions';

COMMENT ON COLUMN users.phone_number_encrypted IS 'Encrypted phone number (encrypted in application layer)';
COMMENT ON COLUMN users.preferences IS 'User preferences stored as JSON (topics, notifications, etc.)';
COMMENT ON COLUMN users.subscription_data IS 'Subscription details stored as JSON';
COMMENT ON COLUMN sessions.session_config IS 'Session-specific configuration stored as JSON';
COMMENT ON COLUMN messages.message_metadata IS 'Message metadata stored as JSON (AI confidence, processing time, etc.)';

-- Display success message
DO $$ BEGIN
    RAISE NOTICE 'Database schema initialized successfully!';
    RAISE NOTICE 'Tables created: users, sessions, messages';
    RAISE NOTICE 'Extensions enabled: uuid-ossp, vector, pg_trgm';
END $$;
