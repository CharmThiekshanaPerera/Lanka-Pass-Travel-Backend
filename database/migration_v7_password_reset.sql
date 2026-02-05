-- Migration to add requires_password_reset column to public.users table
-- This flag will be used to force vendors to reset their auto-generated passwords
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS requires_password_reset BOOLEAN DEFAULT FALSE;
