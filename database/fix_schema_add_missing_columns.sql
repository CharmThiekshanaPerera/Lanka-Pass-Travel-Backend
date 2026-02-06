-- Add missing columns to vendor_services table
-- Detected during verification of service upload

ALTER TABLE public.vendor_services
    ADD COLUMN IF NOT EXISTS not_suitable_for TEXT,
    ADD COLUMN IF NOT EXISTS important_info TEXT,
    ADD COLUMN IF NOT EXISTS cancellation_policy TEXT,
    ADD COLUMN IF NOT EXISTS accessibility_info TEXT;

-- Refresh schema cache
NOTIFY pgrst, 'reload schema';
