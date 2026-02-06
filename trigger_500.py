import requests
import uuid

def test_trigger_500():
    url = "http://localhost:8000/api/auth/register"
    email = f"bug_hunt_{uuid.uuid4().hex[:6]}@ceylonx.com"
    data = {
        "name": "Bug Hunter",
        "email": email,
        "password": "Password123!",
        "role": "admin"
    }
    print(f"Testing registration for {email}...")
    try:
        r = requests.post(url, json=data)
        print(f"Registration Status: {r.status_code}")
        if r.status_code != 200:
            print(f"Registration failed: {r.text}")
            return

        print(f"\nTesting login for {email}...")
        login_url = "http://localhost:8000/api/auth/login"
        login_data = {"username": email, "password": data["password"]}
        r = requests.post(login_url, data=login_data)
        print(f"Login Status: {r.status_code}")
        print(f"Login Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_trigger_500()
