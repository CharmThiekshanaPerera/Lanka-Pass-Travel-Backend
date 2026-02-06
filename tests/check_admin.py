"""
Diagnostic script to check admin user status
"""
import requests

BASE_URL = "http://localhost:8000"

print("="*60)
print("  ADMIN USER DIAGNOSTIC")
print("="*60)

# Test different scenarios
test_credentials = [
    ("admin@lankapass.com", "Admin123!@#"),
    ("admin@test.com", "Admin123!@#"),
]

print("\nTesting login with different credentials...\n")

for email, password in test_credentials:
    print(f"Trying: {email}")
    payload = {"email": email, "password": password}
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ SUCCESS!")
            print(f"    Role: {data.get('user', {}).get('role')}")
            print(f"    Name: {data.get('user', {}).get('name')}")
            print(f"    Token: {data.get('access_token', '')[:30]}...")
            print("\n" + "="*60)
            print("ADMIN USER FOUND AND WORKING!")
            print("="*60)
            print(f"\nUpdate test_with_existing_admin.py:")
            print(f"  ADMIN_EMAIL = \"{email}\"")
            print(f"  ADMIN_PASSWORD = \"{password}\"")
            break
        else:
            print(f"  ✗ Failed: {response.status_code}")
            try:
                error = response.json()
                print(f"    Error: {error.get('detail', 'Unknown')}")
            except:
                pass
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
    
    print()

else:
    print("="*60)
    print("NO ADMIN USER FOUND")
    print("="*60)
    print("\nYou need to create an admin user in Supabase:")
    print("\n1. Go to: https://azrdrjbrwdahwnkuufvw.supabase.co")
    print("2. Authentication → Users → Add user")
    print("3. Email: admin@lankapass.com")
    print("4. Password: Admin123!@#")
    print("\n5. Then run this SQL in SQL Editor:")
    print("""
INSERT INTO public.users (id, email, name, role, is_active)
SELECT 
  id,
  'admin@lankapass.com',
  'System Admin',
  'admin',
  true
FROM auth.users
WHERE email = 'admin@lankapass.com'
ON CONFLICT (id) DO NOTHING;
""")
    print("\n6. Run this script again to verify")
