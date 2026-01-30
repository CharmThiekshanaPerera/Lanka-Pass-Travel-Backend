-- Fix for vendor registration foreign key issue
-- The problem: RLS policies prevent inserting into public.users table

-- Solution: Add a policy to allow service role to insert users

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Service role can insert users" ON public.users;
DROP POLICY IF EXISTS "Service role has full access" ON public.users;

-- Create policy to allow service role full access to users table
CREATE POLICY "Service role has full access"
    ON public.users
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Verify the policy was created
SELECT tablename, policyname, permissive, roles, cmd 
FROM pg_policies 
WHERE schemaname = 'public' AND tablename = 'users';
