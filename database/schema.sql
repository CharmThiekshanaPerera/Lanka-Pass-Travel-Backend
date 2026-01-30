-- ============================================================
-- LANKA PASS TRAVEL - COMPLETE DATABASE SCHEMA
-- ============================================================

-- 0. Cleanup (if running as reset)
-- DROP TABLE IF EXISTS public.vendor_services CASCADE;
-- DROP TABLE IF EXISTS public.vendors CASCADE;
-- DROP TABLE IF EXISTS public.users CASCADE;

-- 1. Create Users table (Extended from Auth)
-- This table mirrors auth.users but adds application-specific fields
CREATE TABLE IF NOT EXISTS public.users (
    id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('user', 'vendor', 'admin', 'manager')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS for users
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Allow service role full access (Critical for backend API)
DROP POLICY IF EXISTS "Service role has full access" ON public.users;
CREATE POLICY "Service role has full access" ON public.users FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Users can view their own profile" ON public.users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Admins can view all users" ON public.users FOR SELECT USING ((auth.jwt() ->> 'role') = 'admin' OR (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin');

-- 2. Create Vendors table
CREATE TABLE IF NOT EXISTS public.vendors (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE UNIQUE,
    
    -- Vendor Basics
    vendor_type VARCHAR(100),
    vendor_type_other TEXT,
    business_name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    contact_person VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone_number VARCHAR(50),
    phone_verified BOOLEAN DEFAULT FALSE,
    operating_areas TEXT[],
    operating_areas_other TEXT,
    
    -- Business Details
    business_reg_number VARCHAR(100),
    business_address TEXT NOT NULL,
    tax_id VARCHAR(100),
    
    -- Bank Details
    bank_name VARCHAR(100),
    bank_name_other TEXT,
    account_holder_name VARCHAR(255),
    account_number VARCHAR(100),
    bank_branch VARCHAR(100),
    
    -- File URLs
    reg_certificate_url TEXT,
    nic_passport_url TEXT,
    tourism_license_url TEXT,
    logo_url TEXT,
    cover_image_url TEXT,
    gallery_urls TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Agreements
    accept_terms BOOLEAN DEFAULT FALSE,
    accept_commission BOOLEAN DEFAULT FALSE,
    accept_cancellation BOOLEAN DEFAULT FALSE,
    grant_rights BOOLEAN DEFAULT FALSE,
    confirm_accuracy BOOLEAN DEFAULT FALSE,
    marketing_permission BOOLEAN DEFAULT FALSE,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'suspended')),
    status_reason TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS for vendors
ALTER TABLE public.vendors ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
DROP POLICY IF EXISTS "Service role has full access" ON public.vendors;
CREATE POLICY "Service role has full access" ON public.vendors FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Vendors can view their own profile" ON public.vendors FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Vendors can update their own profile" ON public.vendors FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Admins can view and manage all vendors" ON public.vendors FOR ALL USING (EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin'));

-- 3. Create Vendor Services table
CREATE TABLE IF NOT EXISTS public.vendor_services (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    vendor_id UUID REFERENCES public.vendors(id) ON DELETE CASCADE,
    
    -- Service Details
    service_name VARCHAR(255) NOT NULL,
    service_category VARCHAR(100),
    service_description TEXT, -- Main description used by backend
    short_description TEXT,   -- Optional short summary
    whats_included TEXT,
    whats_not_included TEXT,
    duration_value INTEGER,
    duration_unit VARCHAR(20),
    languages_offered TEXT[],
    group_size_min INTEGER,
    group_size_max INTEGER,
    daily_capacity INTEGER,
    operating_days TEXT[],
    locations_covered TEXT[],
    image_urls TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Pricing
    currency VARCHAR(10) DEFAULT 'USD',
    retail_price DECIMAL(10,2),
    commission DECIMAL(5,2),
    net_price DECIMAL(10,2),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS for services
ALTER TABLE public.vendor_services ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
DROP POLICY IF EXISTS "Service role has full access" ON public.vendor_services;
CREATE POLICY "Service role has full access" ON public.vendor_services FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Public can view services" ON public.vendor_services FOR SELECT USING (true);
CREATE POLICY "Vendors can manage their own services" ON public.vendor_services FOR ALL USING (
    EXISTS (SELECT 1 FROM public.vendors WHERE id = vendor_services.vendor_id AND user_id = auth.uid())
);
