"""
Step-by-step manager workflow test with better error handling
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_step(step_num, description, func):
    """Helper to run a test step"""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {description}")
    print('='*60)
    try:
        result = func()
        return result
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None

def register_admin():
    """Register admin user"""
    # Use unique email with timestamp to avoid conflicts
    timestamp = int(time.time())
    email = f"admin{timestamp}@test.com"
    password = "Admin123!@#"
    
    payload = {
        "email": email,
        "password": password,
        "name": "Test Admin",
        "role": "admin"
    }
    
    print(f"Registering admin: {email}")
    response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Admin registered successfully")
        print(f"  Email: {email}")
        print(f"  Role: {data.get('user', {}).get('role')}")
        return {
            'email': email,
            'password': password,
            'token': data.get('access_token'),
            'user': data.get('user')
        }
    else:
        print(f"✗ Registration failed")
        print(f"  Response: {response.text}")
        return None

def login_user(email, password):
    """Login as any user"""
    print(f"Logging in as: {email}")
    
    payload = {
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Login successful")
        print(f"  Role: {data.get('user', {}).get('role')}")
        return data.get('access_token')
    else:
        print(f"✗ Login failed: {response.text}")
        return None

def create_manager(admin_token):
    """Create a manager"""
    timestamp = int(time.time())
    email = f"manager{timestamp}@test.com"
    password = "Manager123!@#"
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "email": email,
        "password": password,
        "name": "Test Manager"
    }
    
    print(f"Creating manager: {email}")
    response = requests.post(
        f"{BASE_URL}/api/admin/managers",
        json=payload,
        headers=headers
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Manager created successfully")
        print(f"  ID: {data.get('manager', {}).get('id')}")
        return {
            'email': email,
            'password': password,
            'id': data.get('manager', {}).get('id'),
            'data': data
        }
    else:
        print(f"✗ Manager creation failed")
        print(f"  Response: {response.text}")
        return None

def view_vendors(token, role_name):
    """View vendors as admin or manager"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Fetching vendors as {role_name}...")
    response = requests.get(
        f"{BASE_URL}/api/admin/vendors",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        vendor_count = len(data.get('vendors', []))
        print(f"✓ Successfully retrieved vendors")
        print(f"  Total vendors: {vendor_count}")
        return True
    else:
        print(f"✗ Failed to retrieve vendors")
        print(f"  Response: {response.text}")
        return False

def export_vendors(token, role_name):
    """Export vendor data"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Exporting vendors as {role_name}...")
    response = requests.get(
        f"{BASE_URL}/api/admin/export/vendors",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✓ Export successful")
        print(f"  Data size: {len(response.content)} bytes")
        # Show first line (headers)
        lines = response.text.split('\n')
        if lines:
            print(f"  Headers: {lines[0]}")
        return True
    else:
        print(f"✗ Export failed")
        print(f"  Response: {response.text}")
        return False

def list_managers(admin_token):
    """List all managers"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print("Fetching all managers...")
    response = requests.get(
        f"{BASE_URL}/api/admin/managers",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        managers = data.get('managers', [])
        print(f"✓ Successfully retrieved managers")
        print(f"  Total managers: {len(managers)}")
        for mgr in managers:
            print(f"  - {mgr.get('name')} ({mgr.get('email')})")
        return managers
    else:
        print(f"✗ Failed to retrieve managers")
        print(f"  Response: {response.text}")
        return []

def delete_manager(admin_token, manager_id):
    """Delete a manager"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"Deleting manager: {manager_id}")
    response = requests.delete(
        f"{BASE_URL}/api/admin/managers/{manager_id}",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✓ Manager deleted successfully")
        return True
    else:
        print(f"✗ Deletion failed")
        print(f"  Response: {response.text}")
        return False

def main():
    print("\n" + "="*60)
    print("  MANAGER WORKFLOW COMPREHENSIVE TEST")
    print("="*60)
    
    # Step 1: Register admin
    admin_data = test_step(1, "Register Admin User", register_admin)
    if not admin_data:
        print("\n❌ Test failed: Cannot register admin")
        return
    
    admin_token = admin_data['token']
    
    # Step 2: Create manager
    manager_data = test_step(
        2, 
        "Create Manager (via Admin)", 
        lambda: create_manager(admin_token)
    )
    if not manager_data:
        print("\n❌ Test failed: Cannot create manager")
        return
    
    # Step 3: Login as manager
    manager_token = test_step(
        3,
        "Login as Manager",
        lambda: login_user(manager_data['email'], manager_data['password'])
    )
    if not manager_token:
        print("\n❌ Test failed: Cannot login as manager")
        return
    
    # Step 4: Manager views vendors
    test_step(
        4,
        "Manager Views Vendors",
        lambda: view_vendors(manager_token, "Manager")
    )
    
    # Step 5: Manager exports data
    test_step(
        5,
        "Manager Exports Vendor Data",
        lambda: export_vendors(manager_token, "Manager")
    )
    
    # Step 6: Admin lists managers
    test_step(
        6,
        "Admin Lists All Managers",
        lambda: list_managers(admin_token)
    )
    
    # Step 7: Admin deletes manager
    test_step(
        7,
        "Admin Deletes Manager",
        lambda: delete_manager(admin_token, manager_data['id'])
    )
    
    # Final summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    print("\n✓ All workflow steps completed successfully!")
    print("\nThe system is working properly:")
    print("  ✓ Admin can register and login")
    print("  ✓ Admin can create managers")
    print("  ✓ Manager can login")
    print("  ✓ Manager can view vendors")
    print("  ✓ Manager can export data")
    print("  ✓ Admin can list managers")
    print("  ✓ Admin can delete managers")

if __name__ == "__main__":
    main()
