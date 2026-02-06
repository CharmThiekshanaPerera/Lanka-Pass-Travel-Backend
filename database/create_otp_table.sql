-- OTP Verifications table
CREATE TABLE IF NOT EXISTS public.otp_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    verified BOOLEAN DEFAULT false,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for phone number
CREATE INDEX IF NOT EXISTS idx_otp_phone ON public.otp_verifications(phone_number);

-- RLS
ALTER TABLE public.otp_verifications ENABLE ROW LEVEL SECURITY;

-- Service role access
CREATE POLICY "Service role has full access to otp_verifications"
    ON public.otp_verifications FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');
