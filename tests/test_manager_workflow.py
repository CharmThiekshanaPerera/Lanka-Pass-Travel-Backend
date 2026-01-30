"""
Test script to verify the Manager workflow and system integration.
This script will:
1. Create an admin user (if needed)
2. Create a manager via admin API
3. Login as manager
4. Test manager access to vendor data
5. Test export functionality
6. Clean up test data
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Test credentials
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "Admin123!@#"
ADMIN_NAME = "Test Admin"

MANAGER_EMAIL = "manager@test.com"
MANAGER_PASSWORD = "Manager123!@#"
MANAGER_NAME = "Test Manager"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_admin_register():
    """Try to register an admin user"""
    print_section("1. Registering Admin User")
    
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "name": ADMIN_NAME,
        "role": "admin"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✓ Admin registered successfully")
            return response.json()
        else:
            print("✗ Admin registration failed")
            return None
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None

def test_admin_login():
    """Login as admin"""
    print_section("2. Logging in as Admin")
    
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Admin login successful")
            print(f"Token: {data.get('access_token', '')[:50]}...")
            return data.get('access_token')
        else:
            print(f"✗ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None

def test_create_manager(admin_token):
    """Create a manager using admin token"""
    print_section("3. Creating Manager")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "email": MANAGER_EMAIL,
        "password": MANAGER_PASSWORD,
        "name": MANAGER_NAME
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/managers",
            json=payload,
            headers=headers
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✓ Manager created successfully")
            return response.json()
        else:
            print("✗ Manager creation failed")
            return None
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None

def test_manager_login():
    """Login as manager"""
    print_section("4. Logging in as Manager")
    
    payload = {
        "email": MANAGER_EMAIL,
        "password": MANAGER_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Manager login successful")
            print(f"User Role: {data.get('user', {}).get('role')}")
            return data.get('access_token')
        else:
            print(f"✗ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None

def test_manager_view_vendors(manager_token):
    """Test manager can view vendors"""
    print_section("5. Manager Viewing Vendors")
    
    headers = {"Authorization": f"Bearer {manager_token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/vendors",
            headers=headers
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Manager can view vendors")
            print(f"Total vendors: {len(data.get('vendors', []))}")
            return True
        else:
            print(f"✗ Failed to view vendors: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_manager_export(manager_token):
    """Test manager can export vendor data"""
    print_section("6. Manager Exporting Data")
    
    headers = {"Authorization": f"Bearer {manager_token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/export/vendors",
            headers=headers
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✓ Export successful")
            print(f"Content length: {len(response.content)} bytes")
            print(f"First 200 chars: {response.text[:200]}")
            return True
        else:
            print(f"✗ Export failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_list_managers(admin_token):
    """List all managers"""
    print_section("7. Listing All Managers")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/managers",
            headers=headers
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Managers retrieved")
            print(f"Total managers: {len(data.get('managers', []))}")
            for mgr in data.get('managers', []):
                print(f"  - {mgr.get('name')} ({mgr.get('email')})")
            return data.get('managers', [])
        else:
            print(f"✗ Failed: {response.text}")
            return []
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return []

def cleanup_manager(admin_token, manager_id):
    """Delete the test manager"""
    print_section("8. Cleanup - Deleting Test Manager")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        response = requests.delete(
            f"{BASE_URL}/api/admin/managers/{manager_id}",
            headers=headers
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Manager deleted successfully")
            return True
        else:
            print(f"✗ Deletion failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("  MANAGER WORKFLOW TEST SUITE")
    print("="*60)
    
    # Step 1: Register admin (or login if exists)
    admin_data = test_admin_register()
    
    # Step 2: Login as admin
    admin_token = test_admin_login()
    if not admin_token:
        print("\n❌ Cannot proceed without admin token")
        return
    
    # Step 3: Create manager
    manager_data = test_create_manager(admin_token)
    if not manager_data:
        print("\n❌ Cannot proceed without creating manager")
        return
    
    manager_id = manager_data.get('manager', {}).get('id')
    
    # Step 4: Login as manager
    manager_token = test_manager_login()
    if not manager_token:
        print("\n❌ Cannot proceed without manager token")
        return
    
    # Step 5: Test manager viewing vendors
    test_manager_view_vendors(manager_token)
    
    # Step 6: Test manager export
    test_manager_export(manager_token)
    
    # Step 7: List all managers
    managers = test_list_managers(admin_token)
    
    # Step 8: Cleanup
    if manager_id:
        cleanup_manager(admin_token, manager_id)
    
    print_section("TEST SUMMARY")
    print("✓ All tests completed!")
    print("\nNote: Check the output above for any failures.")

if __name__ == "__main__":
    main()
