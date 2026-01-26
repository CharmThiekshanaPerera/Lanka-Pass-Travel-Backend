import requests
import json

url = "http://localhost:8000/api/auth/login"

payload = {
    "email": "vendor_auth_test_101@lankapass.com",
    "password": "Password123!"
}

headers = {
    'Content-Type': 'application/json'
}

try:
    print(f"Sending login request to {url}...")
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error occurred: {e}")
