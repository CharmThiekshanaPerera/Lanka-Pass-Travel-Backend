import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL", "").strip()
supabase_key = os.getenv("SUPABASE_KEY", "").strip()

if not supabase_url or not supabase_key:
    print("CRITICAL: SUPABASE_URL or SUPABASE_KEY not set!")
    exit(1)

supabase_admin: Client = create_client(supabase_url, supabase_key)

def create_admin():
    email = "admin@lankapass.com"
    password = "Admin123!@#"
    name = "System Admin"
    role = "admin"

    print(f"Creating admin user: {email}")

    try:
        # Check if user already exists (public table)
        res = supabase_admin.table("users").select("*").eq("email", email).execute()
        if res.data:
            print("Admin user already exists in public table.")
            # We might need to reset password if auth exists, but let's try creating auth if missing?
            # Accessing auth admin list is hard.
            # We will try to create auth user, if it fails, it fails.
        
        try:
            auth_res = supabase_admin.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {"role": role, "name": name}
            })
            user_id = auth_res.user.id
            print(f"Auth user created: {user_id}")
            
            # Insert into public table
            user_profile = {
                "id": user_id,
                "email": email,
                "name": name,
                "role": role,
                "is_active": True
            }
            supabase_admin.table("users").upsert(user_profile).execute()
            print("Public user profile created/updated.")
            
        except Exception as e:
            msg = str(e)
            if "already registered" in msg or "unique constraint" in msg:
                print("Auth user likely exists.")
                # Try to get UID from public table to reset password? 
                # Or just assume it works.
                # If login failed earlier, maybe password was different.
                # We can try to update password.
                
                # To update password we need UID.
                # retrieving uid from supabase auth admin is: list_users()
                print("Attempting to reset password...")
                users = supabase_admin.auth.admin.list_users()
                target_user = None
                for u in users:
                    if u.email == email:
                        target_user = u
                        break
                
                if target_user:
                    supabase_admin.auth.admin.update_user_by_id(
                        target_user.id,
                        {"password": password}
                    )
                    print(f"Password updated for {target_user.id}")
                else:
                    print("Could not find auth user to update password.")

            else:
                print(f"Error creating auth user: {msg}")

    except Exception as e:
        print(f"General Error: {e}")

if __name__ == "__main__":
    create_admin()
