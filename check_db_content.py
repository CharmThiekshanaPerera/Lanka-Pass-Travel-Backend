import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

print("Checking database...")
vendors = supabase.table("vendors").select("id, business_name").execute()
print(f"Total Vendors: {len(vendors.data or [])}")

services = supabase.table("vendor_services").select("id, vendor_id, service_name").execute()
print(f"Total Services: {len(services.data or [])}")

if services.data:
    print("\nFirst 5 Services:")
    for s in services.data[:5]:
        print(f" - {s['service_name']} (Vendor ID: {s['vendor_id']})")
else:
    print("\nNo services found in database!")
