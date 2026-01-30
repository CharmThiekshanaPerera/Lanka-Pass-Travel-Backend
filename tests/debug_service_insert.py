import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

try:
    # 1. Create a dummy user
    user_res = supabase.auth.sign_up({"email": "debug_service@test.com", "password": "password123"})
    if not user_res.user:
        # try login
        user_res = supabase.auth.sign_in_with_password({"email": "debug_service@test.com", "password": "password123"})
    
    user_id = user_res.user.id
    print(f"User ID: {user_id}")
    
    # 2. Create dummy vendor
    # Check if exists
    existing = supabase.table("vendors").select("id").eq("user_id", user_id).execute()
    if existing.data:
        vendor_id = existing.data[0]["id"]
    else:
        vendor_data = {
            "user_id": user_id,
            "business_name": "Debug Business",
            "contact_person": "Debug Person",
            "email": "debug_service@test.com",
            "business_address": "Test Address"
        }
        res = supabase.table("vendors").insert(vendor_data).execute()
        vendor_id = res.data[0]["id"]
        
    print(f"Vendor ID: {vendor_id}")
    
    # 3. Try to insert service
    service_data = {
        "vendor_id": vendor_id,
        "service_name": "Debug Service",
        "retail_price": 100.0,
        "commission": 0,
        "net_price": 100.0
    }
    
    print("Attempting to insert service...")
    s_res = supabase.table("vendor_services").insert(service_data).execute()
    print("Success:", s_res.data)
    
except Exception as e:
    print("ERROR:", str(e))
    # Print detailed error if available
    if hasattr(e, 'code'):
        print(f"Code: {e.code}")
    if hasattr(e, 'details'):
        print(f"Details: {e.details}")
    if hasattr(e, 'message'):
        print(f"Message: {e.message}")
