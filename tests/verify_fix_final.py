import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

s1 = create_client(url, key)
s2 = create_client(url, key)

print("Pre-login check...")
s1.auth.admin.list_users() # should work
s2.auth.admin.list_users() # should work

print("Logging in on S1...")
s1.auth.sign_in_with_password({"email": "admin_verify@phyxle.com", "password": "password123"})

# Check result
r1 = "POLLUTED"
try:
    s1.auth.admin.list_users()
    r1 = "STILL ADMIN (UNEXPECTED)"
except Exception as e:
    r1 = "RESTRICTED (EXPECTED)"

r2 = "CLEAN"
try:
    s2.auth.admin.list_users()
    r2 = "CLEAN (EXPECTED)"
except Exception as e:
    r2 = "BROKEN: " + str(e)

print(f"VERIFICATION_RESULT: S1={r1}, S2={r2}")
