-- ============================================================
-- FIX: Add image_urls to vendor_services table
-- ============================================================

ALTER TABLE public.vendor_services
    ADD COLUMN IF NOT EXISTS image_urls TEXT[] DEFAULT ARRAY[]::TEXT[];

-- Refresh schema cache
NOTIFY pgrst, 'reload schema';
