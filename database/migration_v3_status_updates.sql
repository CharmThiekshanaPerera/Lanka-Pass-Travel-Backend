-- Migration V3: Update Status Enums and Add Service Status

-- 1. Update vendors table status check
ALTER TABLE public.vendors DROP CONSTRAINT IF EXISTS vendors_status_check;
ALTER TABLE public.vendors ADD CONSTRAINT vendors_status_check 
    CHECK (status IN ('pending', 'approved', 'active', 'freeze', 'rejected', 'suspended', 'terminated'));

-- 2. Add status column to vendor_services if not exists
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'vendor_services' AND column_name = 'status') THEN
        ALTER TABLE public.vendor_services ADD COLUMN status VARCHAR(50) DEFAULT 'pending';
    END IF;
END $$;

-- 3. Add status check for vendor_services
ALTER TABLE public.vendor_services DROP CONSTRAINT IF EXISTS vendor_services_status_check;
ALTER TABLE public.vendor_services ADD CONSTRAINT vendor_services_status_check 
    CHECK (status IN ('pending', 'approved', 'active', 'freeze', 'rejected', 'draft'));

-- 4. Add admin_notes column to vendors if not exists
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'vendors' AND column_name = 'admin_notes') THEN
        ALTER TABLE public.vendors ADD COLUMN admin_notes TEXT;
    END IF;
END $$;
