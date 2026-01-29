import os
import uuid
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

email = f"test_admin_{uuid.uuid4().hex[:6]}@ceylonx.com"
password = "Password123!"

print(f"Attempting admin.create_user for {email}...")
try:
    res = supabase.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {"role": "admin", "name": "Test Admin"}
    })
    print(f"Success! User ID: {res.user.id}")
except Exception as e:
    print(f"Failed: {e}")
