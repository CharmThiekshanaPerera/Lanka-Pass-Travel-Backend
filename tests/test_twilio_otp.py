import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.sms_service import SmsService

async def test_otp_flow():
    phone_number = input("Enter phone number to test (with country code, e.g., +94...): ").strip()
    if not phone_number:
        phone_number = "+94764627123"
    
    print(f"\nStep 1: Sending OTP to {phone_number} via Text.lk...")
    try:
        success = await SmsService.send_otp(phone_number)
        if success:
            print("SUCCESS: OTP sent successfully! Check your phone.")
            
            otp_code = input("\nEnter the 6-digit OTP you received: ").strip()
            if not otp_code:
                print("ABORTED: No OTP entered.")
                return

            print(f"\nStep 2: Verifying OTP {otp_code} for {phone_number}...")
            is_valid = await SmsService.verify_otp(phone_number, otp_code)
            
            if is_valid:
                print("SUCCESS: Phone number verified successfully!")
            else:
                print("FAILED: Invalid or expired OTP.")
        else:
            print("FAILED: Could not send OTP. Check Text.lk API key and Sender ID.")
    except Exception as e:
        print(f"ERROR: {str(e)}")


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(test_otp_flow())
