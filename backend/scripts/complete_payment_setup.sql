-- ============================================================================
-- Complete Payment System Database Setup
-- ============================================================================
-- This script sets up the entire payment system for the System Design Interview Coach
-- 
-- PREREQUISITES:
-- 1. PostgreSQL database created
-- 2. Users table already exists (from previous setup)
-- 
-- EXECUTION INSTRUCTIONS:
-- Connect to your PostgreSQL database and run:
-- psql -U postgres -d sdicoach -f scripts/complete_payment_setup.sql
-- ============================================================================

\echo '============================================================================'
\echo 'Starting Payment System Database Setup'
\echo '============================================================================'

-- Set client encoding and timezone
SET client_encoding = 'UTF8';
SET timezone = 'UTC';

\echo 'Step 1: Creating payment tables and enums...'
\i payment_tables.sql

\echo 'Step 2: Updating user table for subscription support...'
\i user_table_updates.sql

\echo '============================================================================'
\echo 'Payment System Setup Complete!'
\echo ''
\echo 'Summary of created objects:'
\echo '- Tables: payments, coupons'
\echo '- Enums: payment_status, payment_method, subscription_type, coupon_type, coupon_status'
\echo '- Indexes: 12 performance indexes created'
\echo '- Functions: 3 utility functions for interview limits'
\echo '- Sample data: 3 test coupons inserted'
\echo ''
\echo 'Next steps:'
\echo '1. Update your .env file with Razorpay credentials'
\echo '2. Install razorpay package: pip install razorpay>=1.4.1'
\echo '3. Test the payment endpoints'
\echo '============================================================================'

-- Final verification
\echo 'Verification - Checking created tables:'
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_name IN ('users', 'payments', 'coupons')
ORDER BY table_name;