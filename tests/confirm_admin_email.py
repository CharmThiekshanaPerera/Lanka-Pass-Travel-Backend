import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
# MUST use service role key to update auth.users
supabase_key = os.getenv("SUPABASE_KEY") 
# Note: The key in .env might be anon key. If it's anon, I can't update auth.users.
# But I can try to use the 'check_supabase_key.py' logic or assume the user put the service role key in .env as they are dev.
# Let's try to verify if we have service role.
# If not, I'm stuck unless I disable email confirmation in Supabase (User action) OR I use a loophole.
# Loophole: use the 'check_admin.py' which seemed to work for creating admin but maybe didn't confirm email?

supabase = create_client(supabase_url, supabase_key)

email = "admin_verify@phyxle.com"

try:
    print(f"Confirming email for: {email}")
    # We can't update auth.users directly via JS/Python client usually unless we have service_role and use admin api.
    # supabase.auth.admin.update_user_by_id ...
    
    # 1. Get User ID
    # This requires logging in or admin access.
    # Let's try admin api if key allows.
    
    users = supabase.auth.admin.list_users()
    for u in users:
        if u.email == email:
            print(f"Found user {u.id}. Confirming...")
            supabase.auth.admin.update_user_by_id(
                u.id, 
                {"email_confirm": True, "user_metadata": {"email_verified": True}}
            )
            # The python client might not support 'email_confirm' param directly in update_user_by_id depending on version.
            # Alternate: update attributes
            print("Update sent.")
            break
            
except Exception as e:
    print(f"Error: {e}")
