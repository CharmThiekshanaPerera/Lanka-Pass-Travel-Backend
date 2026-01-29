import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"URL: {url}")
print(f"Key Prefix: {key[:10]}...")

supabase = create_client(url, key)

email = "test_admin_direct@example.com"
password = "Password123!"

print(f"\nAttempting sign_in_with_password for {email}...")
try:
    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    print(f"Login Success! User ID: {res.user.id}")
    print(f"Role: {res.user.user_metadata.get('role')}")
except Exception as e:
    print(f"Login failed: {e}")
