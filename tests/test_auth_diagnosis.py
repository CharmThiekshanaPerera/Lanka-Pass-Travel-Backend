"""
Test script to diagnose Supabase Auth Admin API issues
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Initialize Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

print(f"Supabase URL: {supabase_url}")
print(f"Service Role Key (first 50 chars): {supabase_key[:50]}...")

# Create client
supabase: Client = create_client(supabase_url, supabase_key)

print("\n✅ Supabase client created successfully")

# Test admin API access
print("\n🔍 Testing admin API access...")

try:
    # Try to list users (admin-only operation)
    print("Attempting to list users...")
    users_response = supabase.auth.admin.list_users()
    print(f"✅ Admin API works! Found {len(users_response.users if hasattr(users_response, 'users') else users_response)} users")
except Exception as e:
    print(f"❌ Admin API list_users failed: {e}")

# Test creating a user
print("\n🔍 Testing user creation...")

test_user_params = {
    "email": f"test_{os.urandom(4).hex()}@example.com",
    "password": "TestPass123!",
    "email_confirm": True,
    "user_metadata": {
        "name": "Test User",
        "role": "vendor"
    }
}

print(f"Creating test user: {test_user_params['email']}")

try:
    auth_response = supabase.auth.admin.create_user(test_user_params)
    if auth_response.user:
        print(f"✅ User created successfully! ID: {auth_response.user.id}")
        print(f"   Email: {auth_response.user.email}")
    else:
        print("❌ User creation returned no user object")
except Exception as e:
    error_str = str(e)
    print(f"❌ User creation failed: {error_str}")
    
    # Detailed error analysis
    if "user not allowed" in error_str.lower():
        print("\n📋 DIAGNOSIS: 'User not allowed' error detected!")
        print("   This means Supabase dashboard settings are blocking signups.")
        print("\n   FIX:")
        print("   1. Go to: https://supabase.com/dashboard/project/azrdrjbrwdahwnkuufvw")
        print("   2. Navigate to: Authentication → Providers → Email")
        print("   3. Enable 'Sign ups'")
        print("   4. Disable 'Confirm email' (for development)")
    elif "rate limit" in error_str.lower():
        print("\n📋 DIAGNOSIS: Rate limit exceeded!")
        print("   Too many signup attempts. Wait a few minutes or increase rate limits in dashboard.")
    elif "invalid" in error_str.lower() and "key" in error_str.lower():
        print("\n📋 DIAGNOSIS: Invalid API key!")
        print("   The SUPABASE_KEY might be the anon key instead of service_role key.")
    else:
        print(f"\n📋 Unknown error. Full error: {error_str}")

print("\n" + "="*50)
print("Test completed!")
