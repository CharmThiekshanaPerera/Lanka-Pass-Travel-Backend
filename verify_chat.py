import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def request(method, endpoint, data=None, token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f"Bearer {token}"
    
    body = None
    if data:
        body = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"Error {e.code}: {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"Exception: {str(e)}")
        return None

def run():
    print("1. Logging in as Admin...")
    login_resp = request("POST", "/auth/login", {"email": "admin@lankapass.com", "password": "Admin123!@#"})
    if not login_resp or 'access_token' not in login_resp:
        print("Login failed. Please check credentials or if backend is running.")
        return

    token = login_resp['access_token']
    print("Login successful.")

    print("2. Fetching Vendors...")
    vendors_resp = request("GET", "/admin/vendors", token=token)
    if not vendors_resp or 'vendors' not in vendors_resp:
        print("Failed to fetch vendors.")
        return
    
    vendors = vendors_resp['vendors']
    if not vendors:
        print("No vendors found. Cannot verify chat fully (need a vendor to chat with).")
        # Try a dummy ID just to see if endpoint works
        vendor_id = "dummy_vendor_123"
        print(f"Using dummy vendor ID: {vendor_id}")
    else:
        vendor_id = vendors[0]['id']
        print(f"Using Vendor ID: {vendor_id}")

    print(f"3. Sending Chat Message to {vendor_id}...")
    msg_data = {"message": "Test verification message", "attachments": []}
    send_resp = request("POST", f"/chat/messages/{vendor_id}", msg_data, token=token)
    
    if send_resp:
        print("Message sent successfully.")
        print(json.dumps(send_resp, indent=2))
    else:
        print("Failed to send message.")
        # If dummy vendor, maybe backend rejected? mongo doesn't care about FK usually.
    
    print(f"4. Fetching Messages for {vendor_id}...")
    msgs_resp = request("GET", f"/chat/messages/{vendor_id}", token=token)
    
    if msgs_resp and 'messages' in msgs_resp:
        msgs = msgs_resp['messages']
        print(f"Found {len(msgs)} messages.")
        data_found = False
        for m in msgs:
            if m.get('message') == "Test verification message":
                data_found = True
                print("VERIFIED: Found the sent message!")
                break
        
        if not data_found:
             print("WARNING: Did not find the exact message sent just now.")
             print("Messages:", json.dumps(msgs, indent=2))
    else:
        print("Failed to fetch messages.")

if __name__ == "__main__":
    run()
