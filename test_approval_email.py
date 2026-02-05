
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the current directory to sys.path to import app modules
sys.path.append(os.getcwd())

load_dotenv()

from app.services.email_service import EmailService

async def test_approval_email(email):
    print(f"Testing approval email to: {email}")
    password = "TestPassword123!"
    success = await EmailService.send_approval_credentials(email, password)
    if success:
        print("SUCCESS: Approval email sent successfully via SendGrid.")
    else:
        print("FAILURE: Failed to send approval email. Check console logs and SENDGRID configuration.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_approval_email.py <email_address>")
    else:
        asyncio.run(test_approval_email(sys.argv[1]))
