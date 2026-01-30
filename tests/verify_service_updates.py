import requests
import json
import random
import time

BASE_URL = "http://localhost:8000"

def generate_random_email():
    return f"vendor_test_{random.randint(1000, 9999)}@example.com"

def generate_random_admin_email():
    return f"admin_test_{random.randint(1000, 9999)}@example.com"

def generate_random_manager_email():
    return f"manager_test_{random.randint(1000, 9999)}@example.com"

def test_service_commission_manager():
    print("=== Starting Verification: Service Data, Commission, Manager Role ===")

    # 1. Vendor Registration with Full Service Data
    vendor_email = generate_random_email()
    password = "password123"
    
    vendor_payload = {
        "email": vendor_email,
        "password": password,
        "vendorType": "Tour Operator",
        "businessName": "Lanka Tours",
        "contactPerson": "Nuwan Perera",
        "phoneNumber": "+94771234567",
        "operatingAreas": ["Kandy", "Colombo"],
        "businessAddress": "123 Temple Road, Kandy",
        "bankName": "BOC",
        "accountHolderName": "Nuwan Perera",
        "accountNumber": "123456789",
        "bankBranch": "Kandy",
        "acceptTerms": True,
        "acceptCommission": True,
        "acceptCancellation": True,
        "grantRights": True,
        "confirmAccuracy": True,
        "marketingPermission": True,
        "services": [
            {
                "serviceName": "Kandy City Tour",
                "serviceCategory": "Tours",
                "shortDescription": "A full day tour of Kandy",
                "description": "Experience the culture and history of Kandy.",
                "whatsIncluded": "Transport, Guide, Lunch",
                "whatsNotIncluded": "Tips, Entrance Fees",
                "durationValue": 8,
                "durationUnit": "Hours",
                "retailPrice": 100.0,
                "currency": "USD",
                "languagesOffered": ["English", "German"],
                "groupSizeMin": 2,
                "groupSizeMax": 10,
                "operatingDays": ["Monday", "Wednesday", "Friday"],
                "locationsCovered": ["Temple of Tooth", "Botanical Garden"]
            }
        ]
    }
    
    print(f"\n1. Registering Vendor: {vendor_email}")
    reg_response = requests.post(f"{BASE_URL}/api/vendor/register", json=vendor_payload)
    
    if reg_response.status_code != 201:
        print(f"FAILED: Registration failed with {reg_response.status_code}")
        print(reg_response.text)
        return
    
    vendor_id = reg_response.json()["vendor_id"]
    print(f"SUCCESS: Vendor registered with ID: {vendor_id}")
    
    # 2. Login as Admin to Check Service Data
    # We need an admin user. If not exists, we might need a way to get one or use an existing one.
    # Assuming we have a way to create an admin or use a known one. 
    # For now, let's create a NEW admin using the /api/auth/register endpoint if allowed (it might not default to admin)
    # Actually, we can use the service role key/supabase client to upgrade a user to admin if we were running python script locally accessing DB.
    # But here we are testing API. Let's assume we have a super admin or we can create one.
    # Wait, the app doesn't have a public admin registration.
    # We will use the `check_admin.py` approach or assume we have credentials.
    # Let's try to create an admin first via a loophole or just use a known admin.
    # For this verification script, I will assume I can create an admin directly via Supabase if I had the key.
    # Since I don't have the key in this script, I'll use the API if possible.
    
    # WORKAROUND: I will use the `run_command` tool to create an admin via python script separately if needed.
    # But for this script, let's assume we can login as the vendor and check their own profile to verify service data.
    
    print(f"\n2. Logging in as Vendor to verify Service Data")
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={"email": vendor_email, "password": password})
    if login_response.status_code != 200:
        print(f"FAILED: Login failed")
        return

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    profile_response = requests.get(f"{BASE_URL}/api/vendor/profile", headers=headers)
    if profile_response.status_code != 200:
        print("FAILED: Could not fetch profile")
        return
        
    profile_data = profile_response.json()
    services = profile_data["services"]
    if not services:
        print("FAILED: No services found")
        return
        
    service = services[0]
    print(f"Service Found: {service['service_name']}")
    
    # Verify Fields
    expected_fields = {
        "whats_included": "Transport, Guide, Lunch",
        "duration_value": 8,
        "retail_price": 100.0,
        "commission": 0,
        "net_price": 100.0
    }
    
    failures = []
    for field, expected in expected_fields.items():
        val = service.get(field)
        if field == "retail_price" or field == "net_price":
            val = float(val) if val is not None else 0.0
        
        if val != expected:
            failures.append(f"{field}: Expected {expected}, Got {val}")
            
    if failures:
        print("FAILED: Service data mismatch")
        for f in failures:
            print(f"- {f}")
    else:
        print("SUCCESS: Service data preserved correctly (commission=0, net=retail)")

    service_id = service["id"]

    # 3. Commission Test (Needs Admin)
    # I'll rely on a known admin credential or create one using a separate python script if this fails.
    # Since I cannot easily create an admin via API, I will skip the ACTUAL API call for commission if I don't have admin creds.
    # However, I can try to Create a Manager via Admin (if I have Admin).
    
    # Let's assume we have a "superuser" if possible, or I will create one using the 'check_admin' tool before running this.
    # For now, I will return skipping Admin parts if I can't login.
    
    admin_email = "admin_verify@phyxle.com" 
    admin_pass = "password123" 
    
    print(f"\n3. Commission Update Test (As Admin)")
    # Trying to login as admin
    admin_login = requests.post(f"{BASE_URL}/api/auth/login", json={"email": admin_email, "password": admin_pass})
    
    if admin_login.status_code != 200:
        print(f"WARNING: Could not login as admin. Status: {admin_login.status_code}, Resp: {admin_login.text}")
        print("Skipping Admin/Manager tests.")
        return

    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Update Commission to 15%
    print(f"Setting commission to 15% for service {service_id}")
    comm_payload = {"commission_percent": 15}
    comm_res = requests.patch(f"{BASE_URL}/api/admin/services/{service_id}/commission", json=comm_payload, headers=admin_headers)
    
    if comm_res.status_code == 200:
        data = comm_res.json()
        calc = data["calculation"]
        if calc["net_price"] == 85.0 and calc["commission_amount"] == 15.0:
            print("SUCCESS: Commission updated and Net Price calculated correctly (100 - 15 = 85)")
        else:
            print(f"FAILED: Calculation wrong: {calc}")
    else:
        print(f"FAILED: Update commission failed {comm_res.status_code} {comm_res.text}")

    # 4. Manager Access Test
    print(f"\n4. Manager Restriction Test")
    # Create a manager
    manager_email = generate_random_manager_email()
    manager_payload = {
        "email": manager_email,
        "password": "password123",
        "name": "Test Manager"
    }
    
    create_mgr = requests.post(f"{BASE_URL}/api/admin/managers", json=manager_payload, headers=admin_headers)
    if create_mgr.status_code != 200:
        print("FAILED: Could not create manager")
        return
        
    print(f"Manager created: {manager_email}")
    
    # Login as Manager
    mgr_login = requests.post(f"{BASE_URL}/api/auth/login", json={"email": manager_email, "password": "password123"})
    mgr_token = mgr_login.json()["access_token"]
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}
    
    # Try to View Vendors (Should Succeed)
    view_res = requests.get(f"{BASE_URL}/api/admin/vendors", headers=mgr_headers)
    if view_res.status_code == 200:
        print("SUCCESS: Manager can view vendors")
    else:
        print(f"FAILED: Manager cannot view vendors (Got {view_res.status_code})")
        
    # Try to Approve Vendor (Should Fail)
    print(f"Attempting to approve vendor {vendor_id} as Manager...")
    approve_res = requests.patch(f"{BASE_URL}/api/admin/vendors/{vendor_id}", json={"status": "approved"}, headers=mgr_headers)
    
    if approve_res.status_code == 403:
        print("SUCCESS: Manager prevented from approving vendor (403 Forbidden)")
    else:
        print(f"FAILED: Manager was able to approve/reject or got wrong error: {approve_res.status_code}")

if __name__ == "__main__":
    test_service_commission_manager()
