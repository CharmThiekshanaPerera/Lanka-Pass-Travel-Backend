import requests
import json

url = "http://localhost:8000/api/vendor/register"

payload = {
    "vendorType": "Tour Operator",
    "vendorTypeOther": None,
    "businessName": "Lanka Heritage Tours",
    "legalName": "LHT Pvt Ltd",
    "contactPerson": "Rajesh Fernando",
    "email": "rajesh.fernando@lankaheritage.lk",
    "phoneNumber": "+94772345678",
    "password": "SecurePass456!",
    "operatingAreas": ["Colombo", "Kandy", "Galle"],
    "operatingAreasOther": None,
    "businessRegNumber": "BR123456",
    "businessAddress": "123 Galle Road, Colombo 03",
    "taxId": "TAX-998877",
    "services": [
        {
            "serviceName": "Sigiriya & Dambulla Day Tour",
            "serviceCategory": "Cultural",
            "shortDescription": "Full-day guided tour to ancient rock fortress and cave temples",
            "whatsIncluded": "Transport, Guide, Entrance fees, Lunch",
            "whatsNotIncluded": "Personal expenses, Tips",
            "durationValue": 8,
            "durationUnit": "hours",
            "languagesOffered": ["English", "Sinhala", "Tamil"],
            "groupSizeMin": 2,
            "groupSizeMax": 15,
            "dailyCapacity": 30,
            "operatingDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "locationsCovered": ["Sigiriya", "Dambulla"],
            "retailPrice": 12500.0,
            "currency": "LKR",
            "notSuitableFor": "People with mobility issues",
            "importantInfo": "Wear comfortable walking shoes and modest clothing",
            "cancellationPolicy": "Full refund if cancelled 48h before",
            "accessibilityInfo": "Not suitable for wheelchair users"
        }
    ],
    "bankName": "Bank of Ceylon",
    "bankNameOther": None,
    "accountHolderName": "Lanka Heritage Tours",
    "accountNumber": "9988776655",
    "bankBranch": "Kandy",
    "acceptTerms": True,
    "acceptCommission": True,
    "acceptCancellation": True,
    "grantRights": True,
    "confirmAccuracy": True,
    "marketingPermission": True
}

headers = {
    'Content-Type': 'application/json'
}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error occurred: {e}")
