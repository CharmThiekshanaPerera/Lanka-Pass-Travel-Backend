"""
Diagnostic script for Vendor Registration Failure
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import time
import requests

load_dotenv()

# Initialize Client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

print("="*60)
print("VENDOR REGISTRATION DIAGNOSTIC")
print("="*60)
print(f"URL: {url}")
print(f"Key: {key[:10]}...{key[-5:] if key else ''}")

# Check key role
try:
    import jwt
    decoded = jwt.decode(key, options={"verify_signature": False})
    print(f"Key Role: {decoded.get('role')}")
except Exception as e:
    print(f"Could not decode key: {e}")

timestamp = int(time.time())
email = f"diag_{timestamp}@test.com"
password = "DiagUser123!@#"

print(f"\n1. Attempting sign_up for {email}...")

try:
    # Use sign_up
    auth_res = supabase.auth.sign_up({
        "email": email,
        "password": password,
    })
    
    user_id = auth_res.user.id
    print(f"✓ sign_up successful. User ID: {user_id}")
    
    # Check if user exists via Admin API (requires service_role)
    print("\n2. Verifying user existence in auth.users (via admin api)...")
    try:
        user_get = supabase.auth.admin.get_user_by_id(user_id)
        if user_get:
            print(f"✓ User found in auth.users via Admin API")
            print(f"  ID: {user_get.user.id}")
            print(f"  Email: {user_get.user.email}")
        else:
            print("✗ User NOT found via Admin API (Strange!)")
    except Exception as e:
        print(f"✗ Admin API check failed: {str(e)}")
        print("  (This suggests the key might NOT have full admin privileges)")

    print("\n3. Attempting insert into public.users...")
    try:
        data = {
            "id": user_id,
            "email": email,
            "name": "Diagnostic User",
            "role": "vendor"
        }
        res = supabase.table("users").insert(data).execute()
        print(f"✓ Insert into public.users successful")
        print(res.data)
        
        # Cleanup
        print("\n4. Cleaning up...")
        try:
            supabase.table("users").delete().eq("id", user_id).execute()
            supabase.auth.admin.delete_user(user_id)
            print("✓ Cleanup successful")
        except:
            print("Cleanup failed")
            
        print("\n✅ DIAGNOSTIC PASSED: The backend can create users.")
        
    except Exception as e:
        print(f"\n❌ Insert into public.users FAILED")
        print(f"Error: {str(e)}")
        if "foreign key constraint" in str(e).lower():
            print("\nANALYSIS: This confirms the Foreign Key issue.")
            print("The user ID from sign_up is not visible to the constraint check.")
            print("Possible causes:")
            print("1. Transaction isolation issue (unlikely for API)")
            print("2. 'auth' schema permissions for the postgres role")
            print("3. Triggers on auth.users failing silently?")
            
except Exception as e:
    print(f"\n❌ sign_up FAILED")
    print(f"Error: {str(e)}")

# Also print triggers info if possible
print("\nChecking for triggers requires SQL access. Please run the SQL script provided.")
