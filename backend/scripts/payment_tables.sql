-- ============================================================================
-- Payment System Database Tables
-- ============================================================================
-- This script creates tables for payments, coupons, and related functionality
-- Execute this script in your PostgreSQL database after creating users table
-- ============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- ENUMS (Custom Types)
-- ============================================================================

-- Payment Status Enum
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_status') THEN
        CREATE TYPE payment_status AS ENUM (
            'CREATED',
            'AUTHORIZED', 
            'CAPTURED',
            'FAILED',
            'CANCELLED',
            'REFUNDED'
        );
    END IF;
END $$;

-- Payment Method Enum
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_method') THEN
        CREATE TYPE payment_method AS ENUM (
            'UPI',
            'CREDIT_CARD',
            'DEBIT_CARD',
            'NET_BANKING',
            'WALLET'
        );
    END IF;
END $$;

-- Subscription Type Enum
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscription_type') THEN
        CREATE TYPE subscription_type AS ENUM (
            'LIFETIME',
            'MONTHLY'
        );
    END IF;
END $$;

-- Coupon Type Enum
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'coupon_type') THEN
        CREATE TYPE coupon_type AS ENUM (
            'PERCENTAGE',
            'FIXED_AMOUNT'
        );
    END IF;
END $$;

-- Coupon Status Enum
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'coupon_status') THEN
        CREATE TYPE coupon_status AS ENUM (
            'ACTIVE',
            'INACTIVE',
            'EXPIRED',
            'EXHAUSTED'
        );
    END IF;
END $$;

-- ============================================================================
-- COUPONS TABLE
-- ============================================================================
-- Store coupon codes, discounts, and usage tracking

CREATE TABLE IF NOT EXISTS coupons (
    -- Primary Key
    coupon_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Coupon Identification
    code VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    
    -- Discount Configuration
    coupon_type coupon_type NOT NULL,
    discount_value DECIMAL(10, 2) NOT NULL CHECK (discount_value > 0),
    
    -- Usage Constraints
    minimum_amount DECIMAL(10, 2) CHECK (minimum_amount >= 0),
    maximum_discount DECIMAL(10, 2) CHECK (maximum_discount >= 0),
    usage_limit INTEGER CHECK (usage_limit > 0),
    used_count INTEGER NOT NULL DEFAULT 0 CHECK (used_count >= 0),
    
    -- Validity Period
    valid_from TIMESTAMPTZ NOT NULL,
    valid_until TIMESTAMPTZ NOT NULL,
    
    -- Status
    status coupon_status NOT NULL DEFAULT 'ACTIVE',
    
    -- Metadata
    created_by VARCHAR(255),
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_coupon_valid_period CHECK (valid_until > valid_from),
    CONSTRAINT chk_coupon_usage_limit CHECK (usage_limit IS NULL OR used_count <= usage_limit),
    CONSTRAINT chk_percentage_discount CHECK (
        coupon_type != 'PERCENTAGE' OR discount_value <= 100
    )
);

-- ============================================================================
-- PAYMENTS TABLE
-- ============================================================================
-- Store payment transactions, orders, and Razorpay integration data

CREATE TABLE IF NOT EXISTS payments (
    -- Primary Key
    payment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Foreign Key to Users
    user_id UUID NOT NULL,
    
    -- Payment Order Details
    order_id VARCHAR(255) NOT NULL UNIQUE,
    receipt VARCHAR(255),
    
    -- Amount Information
    amount DECIMAL(10, 2) NOT NULL CHECK (amount >= 0),
    original_amount DECIMAL(10, 2) CHECK (original_amount >= 0),
    discount_amount DECIMAL(10, 2) DEFAULT 0 CHECK (discount_amount >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'INR',
    
    -- Subscription Information
    subscription_type subscription_type,
    
    -- Payment Status and Method
    status payment_status NOT NULL DEFAULT 'CREATED',
    payment_method payment_method,
    
    -- Razorpay Integration Fields
    razorpay_payment_id VARCHAR(255) UNIQUE,
    razorpay_order_id VARCHAR(255) UNIQUE,
    razorpay_signature VARCHAR(255),
    
    -- Coupon Information
    coupon_applied UUID,
    
    -- Error Handling
    failure_reason TEXT,
    
    -- Additional Metadata
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    authorized_at TIMESTAMPTZ,
    captured_at TIMESTAMPTZ,
    
    -- Foreign Key Constraints
    CONSTRAINT fk_payments_user_id 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_payments_coupon_applied 
        FOREIGN KEY (coupon_applied) REFERENCES coupons(coupon_id) ON DELETE SET NULL,
    
    -- Business Logic Constraints
    CONSTRAINT chk_payment_amount_consistency CHECK (
        original_amount IS NULL OR 
        (original_amount >= amount AND original_amount - discount_amount = amount)
    ),
    CONSTRAINT chk_payment_timestamps CHECK (
        authorized_at IS NULL OR authorized_at >= created_at
    ),
    CONSTRAINT chk_capture_after_auth CHECK (
        captured_at IS NULL OR 
        (authorized_at IS NOT NULL AND captured_at >= authorized_at)
    )
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Coupons Indexes
CREATE INDEX IF NOT EXISTS idx_coupons_code_status 
    ON coupons(code, status);
    
CREATE INDEX IF NOT EXISTS idx_coupons_valid_period 
    ON coupons(valid_from, valid_until);
    
CREATE INDEX IF NOT EXISTS idx_coupons_status_usage 
    ON coupons(status, usage_limit, used_count);
    
CREATE INDEX IF NOT EXISTS idx_coupons_created_at 
    ON coupons(created_at);

-- Payments Indexes
CREATE INDEX IF NOT EXISTS idx_payments_user_id 
    ON payments(user_id);
    
CREATE INDEX IF NOT EXISTS idx_payments_user_status 
    ON payments(user_id, status);
    
CREATE INDEX IF NOT EXISTS idx_payments_created_at 
    ON payments(created_at DESC);
    
CREATE INDEX IF NOT EXISTS idx_payments_subscription_type 
    ON payments(subscription_type);
    
CREATE INDEX IF NOT EXISTS idx_payments_order_id 
    ON payments(order_id);
    
CREATE INDEX IF NOT EXISTS idx_payments_razorpay_payment_id 
    ON payments(razorpay_payment_id);
    
CREATE INDEX IF NOT EXISTS idx_payments_status_created 
    ON payments(status, created_at);

-- Composite index for payment history queries
CREATE INDEX IF NOT EXISTS idx_payments_user_status_created 
    ON payments(user_id, status, created_at DESC);

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ============================================================================

-- Function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for coupons table
DROP TRIGGER IF EXISTS update_coupons_updated_at ON coupons;
CREATE TRIGGER update_coupons_updated_at
    BEFORE UPDATE ON coupons
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for payments table
DROP TRIGGER IF EXISTS update_payments_updated_at ON payments;
CREATE TRIGGER update_payments_updated_at
    BEFORE UPDATE ON payments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SAMPLE DATA (Optional - Remove in production)
-- ============================================================================

-- Insert sample coupons for testing
INSERT INTO coupons (
    code, description, coupon_type, discount_value,
    minimum_amount, maximum_discount, usage_limit,
    valid_from, valid_until, created_by
) VALUES 
(
    'WELCOME50',
    'Welcome discount - 50% off on first subscription',
    'PERCENTAGE',
    50.00,
    99.00,
    500.00,
    100,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP + INTERVAL '30 days',
    'system'
),
(
    'SAVE100',
    'Fixed ₹100 discount on any subscription',
    'FIXED_AMOUNT',
    100.00,
    200.00,
    100.00,
    50,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP + INTERVAL '15 days',
    'system'
),
(
    'LIFETIME20',
    'Special 20% discount for lifetime subscriptions',
    'PERCENTAGE',
    20.00,
    500.00,
    200.00,
    25,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP + INTERVAL '7 days',
    'system'
)
ON CONFLICT (code) DO NOTHING;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check table creation
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('payments', 'coupons')
ORDER BY table_name;

-- Check indexes
SELECT 
    indexname,
    tablename,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename IN ('payments', 'coupons')
ORDER BY tablename, indexname;

-- Check sample data
SELECT 
    'Coupons' as table_name,
    COUNT(*) as record_count
FROM coupons
UNION ALL
SELECT 
    'Payments' as table_name,
    COUNT(*) as record_count
FROM payments;

-- ============================================================================
-- CLEANUP (Uncomment only if you need to drop tables)
-- ============================================================================

/*
-- WARNING: This will delete ALL payment and coupon data!
-- Only run this in development environment

DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS coupons CASCADE;

DROP TYPE IF EXISTS payment_status CASCADE;
DROP TYPE IF EXISTS payment_method CASCADE;
DROP TYPE IF EXISTS subscription_type CASCADE;
DROP TYPE IF EXISTS coupon_type CASCADE;
DROP TYPE IF EXISTS coupon_status CASCADE;

DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
*/