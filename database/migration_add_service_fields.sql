-- Migration to add missing columns to vendor_services table
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS service_category_other TEXT;
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS languages_other TEXT;
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS operating_hours_from TEXT;
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS operating_hours_from_period VARCHAR(10) DEFAULT 'AM';
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS operating_hours_to TEXT;
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS operating_hours_to_period VARCHAR(10) DEFAULT 'PM';
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS blackout_dates TEXT[]; -- Array of dates or strings
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS blackout_holidays BOOLEAN DEFAULT FALSE;
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS blackout_weekends BOOLEAN DEFAULT FALSE;
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS advance_booking TEXT;
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS advance_booking_other TEXT;
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS not_suitable_for TEXT;
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS important_info TEXT;
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS cancellation_policy TEXT;
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS accessibility_info TEXT;
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active';
ALTER TABLE public.vendor_services ADD COLUMN IF NOT EXISTS service_time_slots JSONB DEFAULT '[]'::JSONB;

-- Refresh the PostgREST schema cache (Supabase specific, usually happens automatically on DDL changes but good to note)
-- NOTIFY pgrst, 'reload schema';
