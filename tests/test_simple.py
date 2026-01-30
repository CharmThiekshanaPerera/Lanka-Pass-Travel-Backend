"""
Simple test to verify admin can create a manager
"""
import requests
import json

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "Admin123!@#"

print("="*60)
print("SIMPLE MANAGER CREATION TEST")
print("="*60)

# Step 1: Login as admin
print("\n1. Logging in as admin...")
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
)

if login_response.status_code != 200:
    print(f"✗ Login failed: {login_response.text}")
    exit(1)

login_data = login_response.json()
admin_token = login_data.get("access_token")
admin_user = login_data.get("user", {})

print(f"✓ Login successful")
print(f"  Email: {admin_user.get('email')}")
print(f"  Role: {admin_user.get('role')}")
print(f"  Token (first 30 chars): {admin_token[:30]}...")

# Step 2: Try to create a manager
print("\n2. Creating a manager...")
import time
timestamp = int(time.time())
manager_email = f"testmgr{timestamp}@test.com"

headers = {
    "Authorization": f"Bearer {admin_token}",
    "Content-Type": "application/json"
}

manager_payload = {
    "email": manager_email,
    "password": "Manager123!@#",
    "name": "Test Manager"
}

print(f"  Manager email: {manager_email}")
print(f"  Sending request to: {BASE_URL}/api/admin/managers")
print(f"  Headers: Authorization: Bearer {admin_token[:20]}...")

create_response = requests.post(
    f"{BASE_URL}/api/admin/managers",
    json=manager_payload,
    headers=headers
)

print(f"\n  Response status: {create_response.status_code}")
print(f"  Response body: {create_response.text}")

if create_response.status_code == 200:
    print("\n✓ SUCCESS! Manager created")
    manager_data = create_response.json()
    print(json.dumps(manager_data, indent=2))
else:
    print("\n✗ FAILED to create manager")
    print("\nPossible issues:")
    print("  - Token might be invalid or expired")
    print("  - User might not have admin role")
    print("  - Backend endpoint might have an error")
    print("\nCheck the backend logs (python run.py terminal) for more details")
