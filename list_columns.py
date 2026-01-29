import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# Get columns using PostgREST's introspection
info_url = f"{url}/rest/v1/"
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Accept": "application/openapi+json"
}

try:
    with httpx.Client() as client:
        response = client.get(info_url, headers=headers)
        if response.status_code == 200:
            spec = response.json()
            vs = spec.get("definitions", {}).get("vendor_services", {})
            properties = vs.get("properties", {})
            print("Columns in vendor_services:")
            for col in properties:
                print(f" - {col}")
        else:
            print(f"Failed to fetch schema: {response.status_code}")
            print(response.text)
except Exception as e:
    print(f"Error: {e}")
