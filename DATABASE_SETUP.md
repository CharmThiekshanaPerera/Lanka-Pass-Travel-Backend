# Database Setup Instructions

## Issue
The database schema has not been applied to your Supabase instance yet. You need to run the SQL schema to create the necessary tables.

## Steps to Fix

### 1. Apply the Database Schema

1. Go to your Supabase Dashboard: https://azrdrjbrwdahwnkuufvw.supabase.co
2. Navigate to the **SQL Editor** (left sidebar)
3. Click **New Query**
4. Copy the entire contents of `schema.sql` file
5. Paste it into the SQL editor
6. Click **Run** to execute the schema

### 2. Verify Tables Were Created

After running the schema, verify the tables exist:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'vendors', 'vendor_services');
```

You should see all three tables listed.

### 3. Create Your First Admin User

Once the schema is applied, you can create an admin user either:

**Option A: Via Supabase Dashboard**
1. Go to Authentication > Users
2. Click "Add user"
3. Create a user with email/password
4. Then run this SQL to make them an admin:

```sql
INSERT INTO public.users (id, email, name, role, is_active)
VALUES (
  '<user-id-from-auth>',
  'admin@test.com',
  'Admin User',
  'admin',
  true
);
```

**Option B: Via the test script**
After the schema is applied, run:
```bash
python test_manager_workflow.py
```

This will automatically create an admin user and test the full workflow.

## Common Issues

### "User not allowed" error
- This means the database schema hasn't been applied
- Follow Step 1 above to apply the schema

### "relation does not exist" error
- The tables haven't been created
- Apply the schema.sql file in Supabase SQL Editor

### Authentication errors
- Make sure you're using the correct SUPABASE_KEY (service_role key)
- Check that your .env file has the correct credentials

## Testing After Setup

Once the schema is applied, run the test script:

```bash
python test_manager_workflow.py
```

This will:
1. Create an admin user
2. Create a manager user
3. Test manager login
4. Test viewing vendors
5. Test exporting data
6. Clean up test data
