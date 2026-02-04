-- Migration v2: Add Merchant category support and status enhancements

-- 1. Update vendors table
ALTER TABLE public.vendors ADD COLUMN IF NOT EXISTS admin_notes TEXT;

-- Update vendor status constraints
ALTER TABLE public.vendors DROP CONSTRAINT IF EXISTS vendors_status_check;
ALTER TABLE public.vendors ADD CONSTRAINT vendors_status_check 
    CHECK (status IN ('pending', 'approved', 'active', 'freeze', 'rejected', 'suspended'));

-- 2. Update vendor_services table
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS discount_type VARCHAR(50); -- 'percentage', 'amount', 'promotions'
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS discount_value DECIMAL(10,2);
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS promotions TEXT; -- Text for "Buy 1 get 1 Free", etc.

-- Update service status constraints
ALTER TABLE public.vendor_services DROP CONSTRAINT IF EXISTS vendor_services_status_check;
ALTER TABLE public.vendor_services ADD CONSTRAINT vendor_services_status_check 
    CHECK (status IN ('pending', 'approved', 'active', 'freeze', 'rejected'));

-- Provide some comments for the migration
COMMENT ON COLUMN public.vendor_services.discount_type IS 'Type of discount: percentage, amount, or promotions';
COMMENT ON COLUMN public.vendor_services.discount_value IS 'The value of the discount (e.g., 5.00 for 5%)';
COMMENT ON COLUMN public.vendor_services.promotions IS 'Specific promotion wording like Buy 1 get 1 Free';
