import requests
import uuid
import sys

BASE_URL = "http://localhost:8001"

def test_auth_flow(role="user"):
    # 1. Register
    email = f"{role}_{uuid.uuid4().hex[:8]}@example.com"
    password = "Password123!"
    name = f"{role.capitalize()} Tester"
    
    print(f"\n--- Testing {role.capitalize()} Registration ---")
    reg_data = {
        "name": name,
        "email": email,
        "password": password,
        "role": role
    }
    
    try:
        reg_res = requests.post(f"{BASE_URL}/api/auth/register", json=reg_data)
        print(f"Registration Status: {reg_res.status_code}")
        print(f"Registration Response: {reg_res.json()}")
        
        if reg_res.status_code != 200:
            print(f"{role.capitalize()} Registration FAILED")
            return
            
        print(f"{role.capitalize()} Registration SUCCESS")
        
        # Give Supabase a moment to index
        import time
        time.sleep(2)
        
        # 2. Login
        print(f"\n--- Testing {role.capitalize()} Login ---")
        login_data_form = {
            "username": email,
            "password": password
        }
        
        # Try JSON first since some FastAPI setups prefer it
        reg_data_json = {
            "email": email,
            "password": password
        }
        
        print(f"Trying JSON login...")
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=reg_data_json)
        
        if login_res.status_code != 200:
            print(f"JSON Login failed, trying Form data...")
            login_res = requests.post(f"{BASE_URL}/api/auth/login", data=login_data_form)
        print(f"Login Status: {login_res.status_code}")
        
        if login_res.status_code != 200:
            print(f"{role.capitalize()} Login FAILED")
            print(f"Login Response: {login_res.json()}")
            return
            
        print(f"{role.capitalize()} Login SUCCESS")
        
        access_token = login_res.json().get("access_token")
        
        # 3. Verify Token (/api/auth/me)
        print(f"\n--- Testing {role.capitalize()} Token Verification ---")
        headers = {"Authorization": f"Bearer {access_token}"}
        me_res = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        print(f"Me Status: {me_res.status_code}")
        
        if me_res.status_code != 200:
            print(f"{role.capitalize()} Token Verification FAILED")
            return
            
        print(f"{role.capitalize()} Token Verification SUCCESS")
        print(f"--- {role.upper()} AUTH TEST PASSED ---")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    test_auth_flow("user")
    test_auth_flow("admin")
