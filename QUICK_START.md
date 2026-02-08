# Quick Start Guide

## Current Issue
The system needs an initial admin user to be created manually in Supabase before the automated tests can run.

## Solution: Create First Admin User

### Method 1: Via Supabase Dashboard (Recommended)

1. **Go to Supabase Dashboard**: https://azrdrjbrwdahwnkuufvw.supabase.co

2. **Create Auth User**:
   - Navigate to **Authentication** → **Users**
   - Click **"Add user"** → **"Create new user"**
   - Email: `admin@lankapass.com`
   - Password: `Admin123!@#`
   - Click **"Create user"**
   - Copy the **User UID** (you'll need this)

3. **Add to Users Table**:
   - Go to **SQL Editor** → **New query**
   - Run this SQL (replace `<USER_UID>` with the copied UID):

```sql
INSERT INTO public.users (id, email, name, role, is_active)
VALUES (
  '<USER_UID>',
  'admin@lankapass.com',
  'System Admin',
  'admin',
  true
);
```

### Method 2: Direct SQL (If you have psql access)

```sql
-- This requires direct database access
-- Not recommended for Supabase hosted instances
```

## After Creating Admin

Once you have an admin user, test the system:

```bash
python test_with_existing_admin.py
```

This will:
- ✓ Login as the existing admin
- ✓ Create a test manager
- ✓ Test manager login and permissions
- ✓ Test data export
- ✓ Clean up test data

## Alternative: Use Frontend to Create Admin

If you prefer, you can also:
1. Start the frontend application
2. Go to the admin registration page
3. Register with role="admin" (this will use the updated API)

## Next Steps

After creating the first admin:
1. Login to the frontend as admin
2. Use the "Managers" tab to create manager accounts
3. Test the full workflow through the UI

## Deployment References
- AWS EC2 setup: `AWS_EC2_SETUP.md`
- Docker usage: `DOCKER.md`
- CI/CD to EC2: `CI_CD.md`
