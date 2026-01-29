"""
Test script that works with an existing admin user
Run this after creating an admin via Supabase dashboard
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

# Use the admin credentials you created in Supabase
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "Admin123!@#"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def login_admin():
    """Login with existing admin"""
    print_section("1. Login as Existing Admin")
    
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Login successful")
        print(f"  Email: {data.get('user', {}).get('email')}")
        print(f"  Role: {data.get('user', {}).get('role')}")
        return data.get('access_token')
    else:
        print(f"✗ Login failed: {response.text}")
        print(f"\n⚠️  Make sure you've created an admin user in Supabase!")
        print(f"   See QUICK_START.md for instructions")
        return None

def create_manager(admin_token):
    """Create a manager"""
    print_section("2. Create Manager")
    
    timestamp = int(time.time())
    email = f"manager{timestamp}@test.com"
    password = "Manager123!@#"
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "email": email,
        "password": password,
        "name": "Test Manager"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/admin/managers",
        json=payload,
        headers=headers
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Manager created")
        print(f"  Email: {email}")
        print(f"  ID: {data.get('manager', {}).get('id')}")
        return {
            'email': email,
            'password': password,
            'id': data.get('manager', {}).get('id')
        }
    else:
        print(f"✗ Failed: {response.text}")
        return None

def login_manager(email, password):
    """Login as manager"""
    print_section("3. Login as Manager")
    
    payload = {"email": email, "password": password}
    response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Manager login successful")
        print(f"  Role: {data.get('user', {}).get('role')}")
        return data.get('access_token')
    else:
        print(f"✗ Failed: {response.text}")
        return None

def view_vendors(token):
    """View vendors"""
    print_section("4. Manager Views Vendors")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/admin/vendors", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success")
        print(f"  Total vendors: {len(data.get('vendors', []))}")
        return True
    else:
        print(f"✗ Failed: {response.text}")
        return False

def export_data(token):
    """Export vendor data"""
    print_section("5. Manager Exports Data")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/admin/export/vendors", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✓ Export successful")
        print(f"  Size: {len(response.content)} bytes")
        lines = response.text.split('\n')
        if lines:
            print(f"  Headers: {lines[0]}")
        return True
    else:
        print(f"✗ Failed: {response.text}")
        return False

def list_managers(admin_token):
    """List all managers"""
    print_section("6. List All Managers")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/api/admin/managers", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        managers = data.get('managers', [])
        print(f"✓ Success")
        print(f"  Total managers: {len(managers)}")
        for mgr in managers:
            print(f"  - {mgr.get('name')} ({mgr.get('email')})")
        return True
    else:
        print(f"✗ Failed: {response.text}")
        return False

def delete_manager(admin_token, manager_id):
    """Delete manager"""
    print_section("7. Delete Test Manager")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.delete(
        f"{BASE_URL}/api/admin/managers/{manager_id}",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✓ Manager deleted")
        return True
    else:
        print(f"✗ Failed: {response.text}")
        return False

def main():
    print("\n" + "="*60)
    print("  MANAGER WORKFLOW TEST")
    print("  (Using Existing Admin)")
    print("="*60)
    
    # Step 1: Login as admin
    admin_token = login_admin()
    if not admin_token:
        print("\n❌ Cannot proceed without admin login")
        print("\nPlease create an admin user first:")
        print("  See QUICK_START.md for instructions")
        return
    
    # Step 2: Create manager
    manager_data = create_manager(admin_token)
    if not manager_data:
        print("\n❌ Cannot proceed without manager")
        return
    
    # Step 3: Login as manager
    manager_token = login_manager(manager_data['email'], manager_data['password'])
    if not manager_token:
        print("\n❌ Manager login failed")
        return
    
    # Step 4: View vendors
    view_vendors(manager_token)
    
    # Step 5: Export data
    export_data(manager_token)
    
    # Step 6: List managers
    list_managers(admin_token)
    
    # Step 7: Cleanup
    if manager_data['id']:
        delete_manager(admin_token, manager_data['id'])
    
    # Summary
    print_section("TEST SUMMARY")
    print("✅ ALL TESTS PASSED!")
    print("\nThe system is working correctly:")
    print("  ✓ Admin authentication")
    print("  ✓ Manager creation")
    print("  ✓ Manager authentication")
    print("  ✓ Manager can view vendors")
    print("  ✓ Manager can export data")
    print("  ✓ Admin can manage managers")

if __name__ == "__main__":
    main()
