
import os
from pymongo import MongoClient
import certifi
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

def test_connection():
    print(f"Testing connection to: {MONGO_URI.split('@')[-1]}")
    
    # Try 1: with certifi
    try:
        print("\nAttempt 1: With certifi...")
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ Attempt 1 Success!")
        return
    except Exception as e:
        print(f"❌ Attempt 1 Failed: {e}")

    # Try 2: insecure
    try:
        print("\nAttempt 2: Insecure (tlsAllowInvalidCertificates=True)...")
        client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ Attempt 2 Success!")
        return
    except Exception as e:
        print(f"❌ Attempt 2 Failed: {e}")

if __name__ == "__main__":
    test_connection()
