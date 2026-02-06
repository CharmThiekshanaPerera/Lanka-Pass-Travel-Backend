import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"Testing Supabase Admin API")
print(f"URL: {url}")
print(f"Key starts with: {key[:15]}...")

supabase = create_client(url, key)

try:
    # Try to list users (requires service role)
    print("Attempting to list users via admin API...")
    users = supabase.auth.admin.list_users()
    print(f"SUCCESS: Found {len(users)} users.")
except Exception as e:
    print(f"FAILED to list users: {e}")

try:
    # Try a simple select
    print("Attempting to select from public.users...")
    res = supabase.table("users").select("count", count="exact").execute()
    print(f"SUCCESS: Selection worked. Count: {res.count}")
except Exception as e:
    print(f"FAILED to select: {e}")
