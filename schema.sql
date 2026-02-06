-- 1. Create Users table (Extended from Auth)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('user', 'vendor', 'admin')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS for users
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile" ON public.users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Admins can view all users" ON public.users FOR SELECT USING (EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin'));

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
    short_description TEXT,
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
    
    -- Pricing
    retail_price DECIMAL(10,2),
    currency VARCHAR(10) DEFAULT 'LKR',
    
    -- Additional Info
    not_suitable_for TEXT,
    important_info TEXT,
    cancellation_policy TEXT,
    accessibility_info TEXT,
    
    -- Images
    image_urls TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS for services
ALTER TABLE public.vendor_services ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Vendors can manage their own services" ON public.vendor_services FOR ALL USING (EXISTS (SELECT 1 FROM public.vendors WHERE id = vendor_id AND user_id = auth.uid()));
CREATE POLICY "Public can view active services" ON public.vendor_services FOR SELECT USING (TRUE);
CREATE POLICY "Admins can manage all services" ON public.vendor_services FOR ALL USING (EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin'));

-- 4. Create indexes
CREATE INDEX IF NOT EXISTS idx_vendors_user_id ON vendors(user_id);
CREATE INDEX IF NOT EXISTS idx_vendors_status ON vendors(status);
CREATE INDEX IF NOT EXISTS idx_vendor_services_vendor_id ON vendor_services(vendor_id);

-- 5. Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_vendors_updated_at BEFORE UPDATE ON vendors FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_vendor_services_updated_at BEFORE UPDATE ON vendor_services FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
