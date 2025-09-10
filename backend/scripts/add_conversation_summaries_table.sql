-- Add conversation summaries table for memory management
CREATE TABLE conversation_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- Summary content
    summary_text TEXT NOT NULL,
    key_topics JSONB NOT NULL DEFAULT '[]',
    user_performance_notes TEXT DEFAULT '',
    
    -- Summary metadata
    message_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for efficient summary retrieval
CREATE INDEX idx_conversation_summaries_session_id ON conversation_summaries(session_id);
CREATE INDEX idx_conversation_summaries_created_at ON conversation_summaries(created_at DESC);
