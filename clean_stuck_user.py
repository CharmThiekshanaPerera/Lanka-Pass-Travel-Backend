"""
Script to clean up a stuck user account by email.
Use this if you get "User already registered" errors during testing.
"""
import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("Error: .env file not found or missing credentials")
    sys.exit(1)

supabase: Client = create_client(url, key)

def delete_user_by_email(email):
    print(f"Searching for user: {email}...")
    
    # List users to find the ID (Admin API limitation: get_user_by_email not always direct)
    # But checking if we can just re-register? No, need delete.
    # Service role has list_users.
    
    try:
        # Get all users (page 1)
        users = supabase.auth.admin.list_users()
        
        target_user = None
        for u in users:
             if u.email == email:
                 target_user = u
                 break
                 
        if target_user:
            print(f"✓ Found user {email} (ID: {target_user.id})")
            print("Deleting...")
            supabase.auth.admin.delete_user(target_user.id)
            print("✓ User deleted successfully!")
            
            # Also try to clean up public.users content just in case cascade failed
            try:
                supabase.table("users").delete().eq("id", target_user.id).execute()
                print("✓ Public profile cleanup attempted")
            except:
                pass
                
        else:
            print(f"✗ User {email} not found in Auth system.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean_stuck_user.py <email_to_delete>")
        print("Example: python clean_stuck_user.py vendor@test.com")
    else:
        delete_user_by_email(sys.argv[1])
