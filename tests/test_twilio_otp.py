import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.sms_service import SmsService

async def test_send_otp():
    phone_number = "+94764627123"
    print(f"Testing OTP send to: {phone_number}")
    
    try:
        success = await SmsService.send_otp(phone_number)
        if success:
            print("SUCCESS: OTP sent successfully! Please check your phone.")
        else:
            print("FAILED: Failed to send OTP. Check Twilio logs or credentials.")
    except Exception as e:
        print(f"ERROR: An error occurred: {str(e)}")


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(test_send_otp())
