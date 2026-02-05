-- Migration V6: Add missing columns to vendors table for admin editing
ALTER TABLE public.vendors ADD COLUMN IF NOT EXISTS website TEXT;
ALTER TABLE public.vendors ADD COLUMN IF NOT EXISTS payout_frequency VARCHAR(50);

-- Also add admin_notes to vendor_services if needed by other features, 
-- but focusing on vendor profile alignment now.
