-- Migration to add email column to otp_verifications table
ALTER TABLE public.otp_verifications ADD COLUMN IF NOT EXISTS email VARCHAR(255);

-- Index for email
CREATE INDEX IF NOT EXISTS idx_otp_email ON public.otp_verifications(email);
