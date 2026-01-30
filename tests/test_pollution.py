import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

def check_admin():
    try:
        users = supabase.auth.admin.list_users()
        print(f"  ADMIN SUCCESS: Found {len(users)} users")
        return True
    except Exception as e:
        print(f"  ADMIN FAILED: {e}")
        return False

print("Step 1: Admin check on fresh client")
check_admin()

print("\nStep 2: Logging in as a normal user (admin_verify@phyxle.com)")
try:
    # This is a real user I created earlier
    res = supabase.auth.sign_in_with_password({"email": "admin_verify@phyxle.com", "password": "password123"})
    print(f"  Login success. User ID: {res.user.id}")
except Exception as e:
    print(f"  Login failed: {e}")

print("\nStep 3: Admin check after user login")
check_admin()

print("\nStep 4: Manual session clear")
supabase.auth.sign_out()
print("  Signed out")

print("\nStep 5: Admin check after sign out")
check_admin()
