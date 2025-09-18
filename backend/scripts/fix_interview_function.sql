-- ============================================================================
-- Fix for Interview Limit Function
-- ============================================================================
-- This script fixes the can_user_create_interview function to work with 
-- the actual user table structure (no separate user_subscriptions table)
-- Run this to fix the SQL error
-- ============================================================================

-- Drop the existing function first
DROP FUNCTION IF EXISTS can_user_create_interview(UUID);

-- Create the corrected function
CREATE OR REPLACE FUNCTION can_user_create_interview(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    user_record RECORD;
    is_premium BOOLEAN := FALSE;
    subscription_tier TEXT;
    expires_at TIMESTAMPTZ;
BEGIN
    -- Get user subscription details from user table
    SELECT 
        u.interviews_this_month,
        u.interviews_today,
        u.last_interview_date,
        u.subscription_data,
        u.subscription_payment_id
    INTO user_record
    FROM users u
    WHERE u.id = p_user_id;
    
    -- Check if user exists
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Check if user has active subscription
    -- User is premium if they have a subscription_payment_id (successful payment)
    IF user_record.subscription_payment_id IS NOT NULL THEN
        is_premium := TRUE;
    ELSIF user_record.subscription_data IS NOT NULL THEN
        -- Check subscription details in subscription_data JSON
        subscription_tier := user_record.subscription_data->>'tier';
        
        -- Check if user has premium tier
        IF subscription_tier IN ('premium', 'lifetime') THEN
            -- Check if subscription is still active
            IF user_record.subscription_data->>'expires_at' IS NULL THEN
                -- No expiry (lifetime)
                is_premium := TRUE;
            ELSE
                -- Check expiry date
                expires_at := (user_record.subscription_data->>'expires_at')::TIMESTAMPTZ;
                is_premium := expires_at > CURRENT_TIMESTAMP;
            END IF;
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

-- Test the function (this should work now)
SELECT 'Function created successfully' as status;

-- Example test (replace with actual user ID when testing)
-- SELECT can_user_create_interview('your-actual-user-id-here') as can_create_interview;