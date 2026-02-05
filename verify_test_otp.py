import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.services.email_service import EmailService
from dotenv import load_dotenv

load_dotenv()

async def main():
    if len(sys.argv) < 3:
        print("Usage: python verify_test_otp.py <email> <otp_code>")
        return

    email = sys.argv[1]
    otp_code = sys.argv[2]
    print(f"Verifying OTP {otp_code} for {email}...")
    try:
        success = await EmailService.verify_otp(email, otp_code)
        if success:
            print(f"Success! OTP {otp_code} is valid for {email}.")
        else:
            print(f"Failed! OTP {otp_code} is invalid or expired for {email}.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
