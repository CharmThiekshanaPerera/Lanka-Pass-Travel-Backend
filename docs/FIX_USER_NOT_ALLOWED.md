# Fix "User not allowed" Error - Supabase Configuration

The "User not allowed" error when creating vendors or managers means Supabase's authentication settings need adjustment.

## Solution

You need to enable the Admin API in your Supabase project:

### Steps:

1. **Go to your Supabase Dashboard**: https://supabase.com/dashboard
2. **Select your project**: azrdrjbrwdahwnkuufvw
3. **Navigate to**: Authentication → Settings
4. **Find "Email Auth"** section
5. **Enable these settings**:
   - ✅ Enable email confirmations: **OFF** (or set to ON if you want email verification)
   - ✅ Enable email signups: **ON**
   - ✅ Confirm email: **OFF** (for testing, can enable later)

6. **Scroll to "User Management"**:
   - ✅ Allow manual user creation: **ON**

7. **Check "Advanced Settings"**:
   - ✅ Disable email confirmations: **ON** (for development)
   
8. **Save changes**

### Alternative: Check if Service Role Key is Correct

The code uses `supabase.auth.admin.create_user()` which requires the **Service Role Key** (not the anon key).

Verify in your `.env` file:
```
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF6cmRyamJyd2RhaHdua3V1ZnZ3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODkyNTM3NywiZXhwIjoyMDg0NTAxMzc3fQ.GqdzJCAPcFupoLROAGOmAE2ArAw9uguuphjfDUzK5tI
```

This should say `"role":"service_role"` when decoded. You can check at https://jwt.io/

### If Still Having Issues

Try adding this parameter to the create_user call:
```python
admin_user_params = {
    "email": str(vendor_data.email),
    "password": vendor_data.password,
    "email_confirm": True,  # Auto-confirm email
    "user_metadata": {
        "name": vendor_data.contactPerson,
        "role": "vendor",
        "business_name": vendor_data.businessName
    },
    "app_metadata": {}  # Add empty app_metadata
}
```

The issue is likely in the Supabase dashboard settings, not the code.
