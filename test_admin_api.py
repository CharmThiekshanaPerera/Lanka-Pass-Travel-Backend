"""
Verify if Service Role Key works for Admin API
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import time

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"URL: {url}")
print(f"Key: {key[:10]}...")

supabase: Client = create_client(url, key)

email = f"admin_api_test_{int(time.time())}@test.com"
password = "TestPassword123!"

print(f"\nAttempting admin.create_user for {email}...")

try:
    res = supabase.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {"role": "vendor"}
    })
    print("✓ SUCCESS!")
    print(f"User ID: {res.user.id}")
    
    # Cleanup
    supabase.auth.admin.delete_user(res.user.id)
    print("✓ Cleanup successful")
    
except Exception as e:
    print("❌ FAILED")
    print(f"Error: {e}")
    # Print type of error
    print(f"Type: {type(e)}")
