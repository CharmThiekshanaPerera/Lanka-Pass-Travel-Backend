import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# Client A: Resembles the polluted client (used for login)
supabase_a = create_client(url, key)
# Client B: Resembles the dedicated admin client
supabase_admin = create_client(url, key)

def check_admin(client, name):
    try:
        users = client.auth.admin.list_users()
        print(f"  {name} ADMIN SUCCESS: Found {len(users)} users")
        return True
    except Exception as e:
        print(f"  {name} ADMIN FAILED: {e}")
        return False

print("Step 1: Fresh check on both clients")
check_admin(supabase_a, "Client A")
check_admin(supabase_admin, "Admin Client")

print("\nStep 2: Logging in as user on Client A ONLY")
try:
    res = supabase_a.auth.sign_in_with_password({"email": "admin_verify@phyxle.com", "password": "password123"})
    print(f"  Client A logged in. User ID: {res.user.id}")
except Exception as e:
    print(f"  Login failed: {e}")

print("\nStep 3: Checking admin rights again")
check_admin(supabase_a, "Client A")
check_admin(supabase_admin, "Admin Client")

print("\nConclusion:")
if not check_admin(supabase_a, "Client A") and check_admin(supabase_admin, "Admin Client"):
    print("  FIX VERIFIED: Client A is polluted, but Admin Client remains clean and working!")
else:
    print("  Check results carefully.")
