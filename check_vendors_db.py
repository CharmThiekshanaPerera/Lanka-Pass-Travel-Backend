
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def check_vendors():
    print("Checking 'vendors' table...")
    res = supabase.table("vendors").select("id, business_name, status, user_id").execute()
    if res.data:
        print(f"{'ID':<40} | {'Business Name':<30} | {'Status':<10} | {'User ID':<40}")
        print("-" * 130)
        for v in res.data:
            print(f"{v.get('id'):<40} | {v.get('business_name', '')[:30]:<30} | {v.get('status', ''):<10} | {v.get('user_id')}")
    else:
        print("No vendors found.")

if __name__ == "__main__":
    check_vendors()
