-- ============================================================
-- FIX: Remove infinite recursion in users table RLS policy
-- ============================================================

-- Drop the problematic policy
DROP POLICY IF EXISTS "Admins can view all users" ON public.users;

-- Create a new policy that doesn't cause recursion
-- This allows admins to view all users by checking role directly from JWT
CREATE POLICY "Admins can view all users" ON public.users 
FOR SELECT 
USING (
    -- Service role bypasses RLS anyway, but for user-level admin access:
    (auth.jwt() ->> 'role') = 'admin'
    OR
    -- Also allow if the user_metadata has admin role
    (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
);

-- Refresh schema cache
NOTIFY pgrst, 'reload schema';
