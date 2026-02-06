import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"URL: {url}")
# print(f"KEY: {key[:10]}...")

supabase = create_client(url, key)

try:
    # List users in public table
    print("\nListing users in public.users table...")
    res = supabase.table("users").select("*").execute()
    for user in res.data:
        print(f"ID: {user['id']}, Email: {user['email']}, Role: {user['role']}")
except Exception as e:
    print(f"Error listing users: {e}")
