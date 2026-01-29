import os
import jwt
from dotenv import load_dotenv

load_dotenv()

supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_key:
    print("❌ SUPABASE_KEY not found in .env file!")
    exit(1)

print(f"🔍 Checking Supabase Key...")
print(f"Key starts with: {supabase_key[:20]}...")

try:
    # Decode JWT without verification to inspect
    decoded = jwt.decode(supabase_key, options={"verify_signature": False})
    
    print("\n✅ JWT Decoded Successfully:")
    print(f"   Issuer: {decoded.get('iss', 'N/A')}")
    print(f"   Role: {decoded.get('role', 'N/A')}")
    print(f"   Ref: {decoded.get('ref', 'N/A')}")
    
    if decoded.get('role') == 'service_role':
        print("\n✅ This is the SERVICE_ROLE key - Admin API should work!")
        print("\nThe issue is likely in your Supabase dashboard settings:")
        print("1. Go to: https://supabase.com/dashboard/project/azrdrjbrwdahwnkuufvw/auth/users")
        print("2. Settings → Authentication → Email Auth")
        print("3. Make sure 'Enable signup' is ON")
        print("4. Try setting 'Confirm email' to OFF for testing")
    elif decoded.get('role') == 'anon':
        print("\n❌ This is the ANON key - Won't work for admin.create_user()!")
        print("\nYou need to use the SERVICE_ROLE key instead.")
        print("Get it from: https://supabase.com/dashboard/project/azrdrjbrwdahwnkuufvw/settings/api")
        print("Look for 'service_role' secret key (NOT the anon public key)")
    else:
        print(f"\n⚠️  Unknown role: {decoded.get('role')}")
        
except Exception as e:
    print(f"\n❌ Failed to decode JWT: {str(e)}")
    print("The key might be invalid or corrupted.")
