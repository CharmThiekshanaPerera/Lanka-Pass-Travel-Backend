-- ============================================================
-- COMPLETE DATABASE SETUP FOR LANKA PASS TRAVEL
-- Run this entire script in Supabase SQL Editor
-- ============================================================

-- ============================================================
-- STEP 1: CREATE TABLES
-- ============================================================

-- Users table (public profile data)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('user', 'vendor', 'admin', 'manager')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vendors table
CREATE TABLE IF NOT EXISTS public.vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    business_name VARCHAR(255) NOT NULL,
    vendor_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    status_reason TEXT,
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone_number VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    website VARCHAR(255),
    business_registration_number VARCHAR(100),
    tax_id VARCHAR(100),
    bank_name VARCHAR(255),
    account_holder_name VARCHAR(255),
    account_number VARCHAR(100),
    payout_frequency VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vendor Services table
CREATE TABLE IF NOT EXISTS public.vendor_services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id UUID REFERENCES public.vendors(id) ON DELETE CASCADE,
    service_name VARCHAR(255) NOT NULL,
    service_description TEXT,
    currency VARCHAR(10),
    retail_price DECIMAL(10, 2),
    commission DECIMAL(5, 2),
    net_price DECIMAL(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- STEP 2: CREATE INDEXES FOR PERFORMANCE
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON public.users(role);
CREATE INDEX IF NOT EXISTS idx_vendors_user_id ON public.vendors(user_id);
CREATE INDEX IF NOT EXISTS idx_vendors_status ON public.vendors(status);
CREATE INDEX IF NOT EXISTS idx_vendor_services_vendor_id ON public.vendor_services(vendor_id);

-- ============================================================
-- STEP 3: ENABLE ROW LEVEL SECURITY (RLS)
-- ============================================================

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vendors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vendor_services ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- STEP 4: CREATE RLS POLICIES
-- ============================================================

-- Users table policies
DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
CREATE POLICY "Users can view own profile"
    ON public.users FOR SELECT
    USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.users;
CREATE POLICY "Users can update own profile"
    ON public.users FOR UPDATE
    USING (auth.uid() = id);

DROP POLICY IF EXISTS "Service role has full access to users" ON public.users;
CREATE POLICY "Service role has full access to users"
    ON public.users FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- Vendors table policies
DROP POLICY IF EXISTS "Vendors can view own data" ON public.vendors;
CREATE POLICY "Vendors can view own data"
    ON public.vendors FOR SELECT
    USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Vendors can insert own data" ON public.vendors;
CREATE POLICY "Vendors can insert own data"
    ON public.vendors FOR INSERT
    WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "Vendors can update own data" ON public.vendors;
CREATE POLICY "Vendors can update own data"
    ON public.vendors FOR UPDATE
    USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Service role has full access to vendors" ON public.vendors;
CREATE POLICY "Service role has full access to vendors"
    ON public.vendors FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- Vendor services table policies
DROP POLICY IF EXISTS "Vendor services viewable by vendor" ON public.vendor_services;
CREATE POLICY "Vendor services viewable by vendor"
    ON public.vendor_services FOR SELECT
    USING (vendor_id IN (SELECT id FROM public.vendors WHERE user_id = auth.uid()));

DROP POLICY IF EXISTS "Vendor services insertable by vendor" ON public.vendor_services;
CREATE POLICY "Vendor services insertable by vendor"
    ON public.vendor_services FOR INSERT
    WITH CHECK (vendor_id IN (SELECT id FROM public.vendors WHERE user_id = auth.uid()));

DROP POLICY IF EXISTS "Service role has full access to vendor_services" ON public.vendor_services;
CREATE POLICY "Service role has full access to vendor_services"
    ON public.vendor_services FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- ============================================================
-- STEP 5: CREATE TRIGGERS FOR UPDATED_AT
-- ============================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for users table
DROP TRIGGER IF EXISTS update_users_updated_at ON public.users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for vendors table
DROP TRIGGER IF EXISTS update_vendors_updated_at ON public.vendors;
CREATE TRIGGER update_vendors_updated_at
    BEFORE UPDATE ON public.vendors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- STEP 6: GRANT PERMISSIONS
-- ============================================================

GRANT ALL ON public.users TO authenticated;
GRANT ALL ON public.vendors TO authenticated;
GRANT ALL ON public.vendor_services TO authenticated;

GRANT ALL ON public.users TO service_role;
GRANT ALL ON public.vendors TO service_role;
GRANT ALL ON public.vendor_services TO service_role;

-- ============================================================
-- VERIFICATION QUERIES
-- ============================================================

-- Run these to verify everything was created:

-- Check tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'vendors', 'vendor_services')
ORDER BY table_name;

-- Check RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('users', 'vendors', 'vendor_services');

-- Check policies exist
SELECT tablename, policyname 
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- ============================================================
-- SETUP COMPLETE!
-- ============================================================
-- Next step: Create your admin user through Supabase Dashboard UI
-- Authentication → Users → Add user
-- Then run the admin user insert script
-- ============================================================
