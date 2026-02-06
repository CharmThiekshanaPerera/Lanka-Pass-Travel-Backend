-- Fix recursive policies on users table
DROP POLICY IF EXISTS "Admins can view all users" ON public.users;
CREATE POLICY "Admins can view all users" ON public.users 
FOR SELECT 
USING (
  (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
  OR 
  (auth.jwt() ->> 'role') = 'service_role'
);

-- Also fix vendors policy if it has recursion
DROP POLICY IF EXISTS "Admins can view and manage all vendors" ON public.vendors;
CREATE POLICY "Admins can view and manage all vendors" ON public.vendors 
FOR ALL 
USING (
  (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
  OR 
  (auth.jwt() ->> 'role') = 'service_role'
);

-- Ensure service role has full access (redundant but safe)
DROP POLICY IF EXISTS "Service role has full access" ON public.users;
CREATE POLICY "Service role has full access" ON public.users FOR ALL USING (auth.role() = 'service_role');
