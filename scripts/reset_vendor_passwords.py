"""
Script to reset all existing vendor passwords to '123456'
This is needed because vendors created before the default password change
have randomly generated passwords.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

# Create Supabase client with service role key (admin access)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def reset_vendor_passwords():
    """Reset all vendor passwords to '123456'"""
    
    print("Fetching all vendors from database...")
    
    # Get all users with role 'vendor'
    result = supabase.table("users").select("id, email, role").eq("role", "vendor").execute()
    vendors = result.data
    
    if not vendors:
        print("No vendors found in database")
        return
    
    print(f"\nFound {len(vendors)} vendor(s):")
    for vendor in vendors:
        print(f"  - {vendor['email']}")
    
    print(f"\n{'='*60}")
    print("Resetting passwords to '123456'...")
    print(f"{'='*60}\n")
    
    success_count = 0
    error_count = 0
    
    for vendor in vendors:
        try:
            # Update password using Admin API
            supabase.auth.admin.update_user_by_id(
                vendor['id'],
                {
                    "password": "123456"
                }
            )
            print(f"[OK] Reset password for: {vendor['email']}")
            success_count += 1
        except Exception as e:
            print(f"[ERROR] Failed to reset password for {vendor['email']}: {str(e)}")
            error_count += 1
    
    print(f"\n{'='*60}")
    print(f"Summary: {success_count} successful, {error_count} failed")
    print(f"{'='*60}")
    print("\nAll vendors can now login with password: 123456")

if __name__ == "__main__":
    reset_vendor_passwords()
