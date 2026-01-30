"""
Direct API test to diagnose the issue
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("Testing API Endpoints...")
print("="*60)

# Test 1: Check if server is running
print("\n1. Testing server health...")
try:
    response = requests.get(f"{BASE_URL}/docs")
    print(f"✓ Server is running (Status: {response.status_code})")
except Exception as e:
    print(f"✗ Server not responding: {e}")
    exit(1)

# Test 2: Try to register with minimal data
print("\n2. Testing user registration...")
payload = {
    "email": "testuser@example.com",
    "password": "Test123!@#",
    "name": "Test User",
    "role": "user"
}

response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code != 200:
    print("\n3. Let's check the detailed error...")
    try:
        error_detail = response.json()
        print(f"Error Detail: {json.dumps(error_detail, indent=2)}")
    except:
        print(f"Raw error: {response.text}")
    
    # The error might be about Supabase admin permissions
    print("\n⚠️  The error 'User not allowed' suggests:")
    print("   - The SUPABASE_KEY might not have admin privileges")
    print("   - You need to use the 'service_role' key, not 'anon' key")
    print("   - Check your .env file and ensure SUPABASE_KEY is the service_role key")
else:
    print("✓ Registration successful!")
    data = response.json()
    print(f"User created: {data.get('user', {}).get('email')}")
