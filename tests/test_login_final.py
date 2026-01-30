import requests

def test_login(port):
    print(f"\n--- Testing Login on Port {port} ---")
    url = f"http://localhost:{port}/api/auth/login"
    data = {
        "email": "test_admin_direct@example.com",
        "password": "Password123!"
    }
    try:
        r = requests.post(url, json=data)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login(8000)
    test_login(8081)
