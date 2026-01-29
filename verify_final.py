import requests
import uuid
import time

BASE_URL = "http://localhost:8081"

def test_auth(role):
    email = f"test_{role}_{uuid.uuid4().hex[:6]}@ceylonx.com"
    password = "Password123!"
    name = f"{role.capitalize()} Tester"
    
    print(f"\n>>> Testing {role.upper()} Flow")
    
    # 1. Register
    reg_data = {"name": name, "email": email, "password": password, "role": role}
    r = requests.post(f"{BASE_URL}/api/auth/register", json=reg_data)
    if r.status_code != 200:
        print(f"Registration failed: {r.text}")
        return False
    print(f"Registration Success: {email}")
    
    # Wait for Supabase
    time.sleep(1)
    
    # 2. Login
    login_data = {"username": email, "password": password}
    r = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    if r.status_code != 200:
        print(f"Login failed: {r.text}")
        return False
    print(f"Login Success: Token received")
    
    token = r.json().get("access_token")
    
    # 3. Me
    r = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    if r.status_code != 200:
        print(f"Me failed: {r.text}")
        return False
    print(f"Me Success: Role is {r.json().get('role')}")
    
    return True

if __name__ == "__main__":
    success_user = test_auth("user")
    success_admin = test_auth("admin")
    
    if success_user and success_admin:
        print("\n=== ALL AUTH FLOWS VERIFIED SUCCESSFULLY ===")
    else:
        print("\n=== AUTH VERIFICATION FAILED ===")
