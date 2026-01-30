import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

admin_url = f"{url}/auth/v1/admin/users"
headers = {
    "Authorization": f"Bearer {key}",
    "apiKey": key,
    "Content-Type": "application/json"
}

data = {
    "email": "test_admin_raw@example.com",
    "password": "Password123!",
    "email_confirm": True,
    "user_metadata": {"role": "manager", "name": "Raw Test"}
}

print(f"Testing raw POST to {admin_url}")
try:
    with httpx.Client() as client:
        response = client.post(admin_url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
