# Troubleshooting: Admin User Not Found

## The Problem
The INSERT query returned no rows because there's no user with email `admin@lankapass.com` in the `auth.users` table.

## Solution: Verify and Create User

### Step 1: Check if user exists in auth.users

Run this SQL in Supabase SQL Editor:

```sql
SELECT id, email, created_at 
FROM auth.users 
WHERE email = 'admin@lankapass.com';
```

**If this returns NO ROWS**: The user doesn't exist in Authentication. Go to Step 2.

**If this returns a row**: The user exists. Go to Step 3.

---

### Step 2: Create User in Supabase Authentication

You MUST create the user through the Supabase Dashboard UI first:

1. In Supabase Dashboard: https://azrdrjbrwdahwnkuufvw.supabase.co
2. Click **Authentication** in the left sidebar
3. Click **Users** tab
4. Click the **"Add user"** button (top right)
5. Select **"Create new user"**
6. Fill in:
   - **Email**: `admin@lankapass.com`
   - **Password**: `Admin123!@#`
   - **Auto Confirm User**: ✓ (check this box)
7. Click **"Create user"**

**IMPORTANT**: You MUST do this through the UI. SQL INSERT into auth.users won't work.

---

### Step 3: After creating the auth user, add to public.users

Now run this SQL:

```sql
-- First, verify the auth user exists
SELECT id, email FROM auth.users WHERE email = 'admin@lankapass.com';

-- If you see a row above, run this:
INSERT INTO public.users (id, email, name, role, is_active)
SELECT 
  id,
  'admin@lankapass.com',
  'System Admin',
  'admin',
  true
FROM auth.users
WHERE email = 'admin@lankapass.com'
ON CONFLICT (id) DO NOTHING;

-- Verify it was added:
SELECT id, email, name, role FROM public.users WHERE email = 'admin@lankapass.com';
```

You should see the admin user in the final SELECT.

---

### Step 4: Test Login

Run the diagnostic script:

```bash
python check_admin.py
```

**Expected output**:
```
✓ SUCCESS!
  Role: admin
  Name: System Admin
```

---

## Alternative: Use a Different Email

If you already created a user with a different email in Supabase Authentication, you can use that instead:

1. Check what users exist:
```sql
SELECT id, email FROM auth.users;
```

2. Pick one and add it to public.users with admin role:
```sql
INSERT INTO public.users (id, email, name, role, is_active)
VALUES (
  '<copy-the-id-here>',
  '<copy-the-email-here>',
  'System Admin',
  'admin',
  true
)
ON CONFLICT (id) DO NOTHING;
```

3. Update `test_with_existing_admin.py` with that email and password.

---

## Common Mistakes

❌ **Trying to INSERT directly into auth.users** - This won't work. Use the UI.

❌ **Forgetting to check "Auto Confirm User"** - User won't be able to login.

❌ **Wrong password** - Make sure it matches what you set.

❌ **Running INSERT before creating auth user** - auth.users must have the user first.

---

## Quick Checklist

- [ ] User created in Authentication → Users (via UI)
- [ ] User appears in `SELECT * FROM auth.users WHERE email = 'admin@lankapass.com'`
- [ ] INSERT into public.users completed successfully
- [ ] User appears in `SELECT * FROM public.users WHERE email = 'admin@lankapass.com'`
- [ ] Role is 'admin' (not 'user' or 'vendor')
- [ ] `python check_admin.py` shows SUCCESS
