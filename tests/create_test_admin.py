import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

email = "admin_verify@phyxle.com"
password = "password123"

# 1. Sign Up/In
try:
    print(f"Creating/Logging in admin: {email}")
    res = supabase.auth.sign_up({"email": email, "password": password})
    user = res.user
    if not user:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        user = res.user
        
    print(f"User ID: {user.id}")
    
    # 2. Update Metadata/Table
    # Assuming role is stored in public.users or metadata
    print("Updating role to 'admin'...")
    supabase.table("users").update({"role": "admin"}).eq("id", user.id).execute()
    
    # Also update metadata if possible (requires service role, but we try standard first)
    # The backend often checks metadata or the table. app/main.py uses Dependency get_current_user which likely checks the DB or Metadata.
    # Looking at schema.sql viewed earlier: 
    # CREATE TABLE public.users ... role VARCHAR ...
    
    print("Admin setup complete.")

except Exception as e:
    print(f"Error: {e}")
