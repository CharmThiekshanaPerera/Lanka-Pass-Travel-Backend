-- Migration to make phone_number nullable in otp_verifications table
-- This allows email-only OTPs to be stored correctly
ALTER TABLE public.otp_verifications ALTER COLUMN phone_number DROP NOT NULL;
