import requests
import sys

BASE_URL = "http://localhost:8000"

def check_endpoint():
    print(f"Checking {BASE_URL}/docs...")
    try:
        r = requests.get(f"{BASE_URL}/docs")
        print(f"Server status: {r.status_code}")
        if r.status_code == 200:
            print("Server is UP.")
        else:
            print("Server seems DOWN or Error.")
            return False
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
    return True

def clean_user(email):
    # We need the service role key to delete users via admin API
    # Since we can't easily import from here without env setup, let's just warn
    print(f"\nTo fix 'User already registered':")
    print(f"1. Go to Supabase Dashboard > Authentication > Users")
    print(f"2. Search for '{email}'")
    print(f"3. Delete the user")
    print("\nOR run the 'clean_user.py' script I will provide next.")

if __name__ == "__main__":
    if check_endpoint():
        # Try to ping the upload endpoint (Method Not Allowed 405 is good, 404 is bad)
        try:
            r = requests.post(f"{BASE_URL}/api/vendor/upload-file")
            print(f"Upload endpoint status: {r.status_code}")
            if r.status_code == 422: # Missing file/form
                print("✓ Upload endpoint exists (422 is expected for missing data)")
            elif r.status_code == 404:
                print("❌ Upload endpoint NOT FOUND")
            else:
                print(f"Upload endpoint returned: {r.status_code}")
        except:
            pass
