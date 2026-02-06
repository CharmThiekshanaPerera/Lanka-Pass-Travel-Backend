-- ============================================================
-- FIX: Update Database Schema to Match Application Code
-- This adds the missing columns that are causing the registration error
-- ============================================================

-- 1. FIX VENDORS TABLE
-- Rename columns to match schema.sql if they exist with old names
DO $$
BEGIN
    IF EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='vendors' AND column_name='address') THEN
        ALTER TABLE public.vendors RENAME COLUMN address TO business_address;
    END IF;
    
    IF EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='vendors' AND column_name='business_registration_number') THEN
        ALTER TABLE public.vendors RENAME COLUMN business_registration_number TO business_reg_number;
    END IF;
END $$;

-- Add missing columns to vendors
ALTER TABLE public.vendors
    ADD COLUMN IF NOT EXISTS vendor_type_other TEXT,
    ADD COLUMN IF NOT EXISTS legal_name VARCHAR(255),
    ADD COLUMN IF NOT EXISTS phone_verified BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS operating_areas TEXT[],
    ADD COLUMN IF NOT EXISTS operating_areas_other TEXT,
    
    -- Ensure these exist (renamed above, but if create failed)
    ADD COLUMN IF NOT EXISTS business_reg_number VARCHAR(100),
    ADD COLUMN IF NOT EXISTS business_address TEXT,
    
    -- Bank details extras
    ADD COLUMN IF NOT EXISTS bank_name_other TEXT,
    ADD COLUMN IF NOT EXISTS bank_branch VARCHAR(100),
    
    -- File URLs
    ADD COLUMN IF NOT EXISTS reg_certificate_url TEXT,
    ADD COLUMN IF NOT EXISTS nic_passport_url TEXT,
    ADD COLUMN IF NOT EXISTS tourism_license_url TEXT,
    ADD COLUMN IF NOT EXISTS logo_url TEXT,
    ADD COLUMN IF NOT EXISTS cover_image_url TEXT,
    ADD COLUMN IF NOT EXISTS gallery_urls TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Agreements (The specific error source!)
    ADD COLUMN IF NOT EXISTS accept_terms BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS accept_commission BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS accept_cancellation BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS grant_rights BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS confirm_accuracy BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS marketing_permission BOOLEAN DEFAULT FALSE;

-- 2. FIX VENDOR SERVICES TABLE
ALTER TABLE public.vendor_services
    ADD COLUMN IF NOT EXISTS service_category VARCHAR(100),
    -- Allow service_description to map to short_description if needed, 
    -- but for now verify what main.py uses. 
    -- main.py uses 'service_description'. 
    -- schema.sql uses 'short_description'.
    -- We'll add 'service_description' to be safe for current code.
    ADD COLUMN IF NOT EXISTS service_description TEXT, 
    
    ADD COLUMN IF NOT EXISTS short_description TEXT,
    ADD COLUMN IF NOT EXISTS whats_included TEXT,
    ADD COLUMN IF NOT EXISTS whats_not_included TEXT,
    ADD COLUMN IF NOT EXISTS duration_value INTEGER,
    ADD COLUMN IF NOT EXISTS duration_unit VARCHAR(20),
    ADD COLUMN IF NOT EXISTS languages_offered TEXT[],
    ADD COLUMN IF NOT EXISTS group_size_min INTEGER,
    ADD COLUMN IF NOT EXISTS group_size_max INTEGER,
    ADD COLUMN IF NOT EXISTS daily_capacity INTEGER,
    ADD COLUMN IF NOT EXISTS operating_days TEXT[],
    ADD COLUMN IF NOT EXISTS locations_covered TEXT[],
    
    -- Ensure pricing fields exist
    ADD COLUMN IF NOT EXISTS currency VARCHAR(10),
    ADD COLUMN IF NOT EXISTS commission DECIMAL(5, 2),
    ADD COLUMN IF NOT EXISTS net_price DECIMAL(10, 2);

-- 3. REFRESH CACHE (Not a SQL command, but notifying Supabase)
NOTIFY pgrst, 'reload schema';

-- 4. VERIFY
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'vendors' 
ORDER BY column_name;
