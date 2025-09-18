-- ============================================================================
-- User Table Updates for Payment System Integration
-- ============================================================================
-- This script adds subscription tracking and interview limits to users table
-- Run this AFTER creating the payment tables
-- ============================================================================

-- ============================================================================
-- ADD SUBSCRIPTION AND INTERVIEW TRACKING COLUMNS
-- ============================================================================

-- Add subscription tracking columns to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS interviews_this_month INTEGER DEFAULT 0 CHECK (interviews_this_month >= 0),
ADD COLUMN IF NOT EXISTS interviews_today INTEGER DEFAULT 0 CHECK (interviews_today >= 0),
ADD COLUMN IF NOT EXISTS last_interview_date DATE,
ADD COLUMN IF NOT EXISTS subscription_payment_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS subscription_upgraded_at TIMESTAMPTZ;

-- ============================================================================
-- UPDATE EXISTING USER PROFILES FOR SUBSCRIPTION SUPPORT
-- ============================================================================

-- Update existing users to have proper subscription defaults
UPDATE users 
SET 
    interviews_this_month = COALESCE(interviews_this_month, 0),
    interviews_today = COALESCE(interviews_today, 0)
WHERE interviews_this_month IS NULL OR interviews_today IS NULL;

-- ============================================================================
-- CREATE INDEXES FOR PERFORMANCE
-- ============================================================================

-- Index for interview tracking queries
CREATE INDEX IF NOT EXISTS idx_users_interview_tracking 
    ON users(interviews_this_month, interviews_today, last_interview_date);

-- Index for subscription queries  
CREATE INDEX IF NOT EXISTS idx_users_subscription_payment 
    ON users(subscription_payment_id) WHERE subscription_payment_id IS NOT NULL;

-- ============================================================================
-- CREATE FUNCTIONS FOR INTERVIEW LIMIT MANAGEMENT
-- ============================================================================

-- Function to reset daily interview counts
CREATE OR REPLACE FUNCTION reset_daily_interview_counts()
RETURNS void AS $$
BEGIN
    UPDATE users 
    SET 
        interviews_today = 0,
        updated_at = CURRENT_TIMESTAMP
    WHERE interviews_today > 0;
    
    RAISE NOTICE 'Reset daily interview counts for all users';
END;
$$ LANGUAGE plpgsql;

-- Function to reset monthly interview counts
CREATE OR REPLACE FUNCTION reset_monthly_interview_counts()
RETURNS void AS $$
BEGIN
    UPDATE users 
    SET 
        interviews_this_month = 0,
        interviews_today = 0,
        updated_at = CURRENT_TIMESTAMP
    WHERE interviews_this_month > 0;
    
    RAISE NOTICE 'Reset monthly interview counts for all users';
END;
$$ LANGUAGE plpgsql;

-- Function to check if user can create interview
CREATE OR REPLACE FUNCTION can_user_create_interview(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    user_record RECORD;
    is_premium BOOLEAN := FALSE;
BEGIN
    -- Get user subscription details from user profile JSON
    SELECT 
        u.interviews_this_month,
        u.interviews_today,
        u.last_interview_date,
        u.profile,
        u.subscription_payment_id
    INTO user_record
    FROM users u
    WHERE u.id = p_user_id;
    
    -- Check if user exists
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Check if user has active subscription
    -- User is premium if they have a subscription_payment_id or subscription data in profile
    IF user_record.subscription_payment_id IS NOT NULL THEN
        is_premium := TRUE;
    ELSIF user_record.profile IS NOT NULL THEN
        -- Check subscription details in profile JSON
        -- Profile contains subscription_details with is_active, is_lifetime, expires_at
        is_premium := COALESCE(
            (user_record.profile->'subscription_details'->>'is_active')::BOOLEAN,
            FALSE
        );
        
        -- Additional check for lifetime subscription
        IF NOT is_premium THEN
            is_premium := COALESCE(
                (user_record.profile->'subscription_details'->>'is_lifetime')::BOOLEAN,
                FALSE
            );
        END IF;
        
        -- Additional check for active monthly subscription
        IF NOT is_premium THEN
            is_premium := CASE
                WHEN user_record.profile->'subscription_details'->>'expires_at' IS NOT NULL
                THEN (user_record.profile->'subscription_details'->>'expires_at')::TIMESTAMPTZ > CURRENT_TIMESTAMP
                ELSE FALSE
            END;
        END IF;
    END IF;
    
    -- Premium users can always create interviews
    IF is_premium THEN
        RETURN TRUE;
    END IF;
    
    -- Free users have 2 interviews per month limit
    IF COALESCE(user_record.interviews_this_month, 0) >= 2 THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check new columns were added
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN (
    'interviews_this_month', 
    'interviews_today', 
    'last_interview_date',
    'subscription_payment_id',
    'subscription_upgraded_at'
)
ORDER BY column_name;

-- Check user interview limits
SELECT 
    COUNT(*) as total_users,
    AVG(interviews_this_month) as avg_monthly_interviews,
    AVG(interviews_today) as avg_daily_interviews,
    COUNT(CASE WHEN subscription_payment_id IS NOT NULL THEN 1 END) as premium_users
FROM users;

-- Test interview limit function
SELECT can_user_create_interview('00000000-0000-0000-0000-000000000000') as can_create_test;

-- ============================================================================
-- SAMPLE UPDATES (Optional - for testing)
-- ============================================================================

/*
-- Update a test user to have some interview history
UPDATE users 
SET 
    interviews_this_month = 1,
    interviews_today = 0,
    last_interview_date = CURRENT_DATE - INTERVAL '1 day'
WHERE email = 'test@example.com';
*/