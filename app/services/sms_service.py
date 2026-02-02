from twilio.rest import Client
import random
import logging
from datetime import datetime, timedelta
from app.config import settings
from app.database.supabase_client import SupabaseManager

logger = logging.getLogger(__name__)

class SmsService:
    client = None

    @classmethod
    def get_client(cls):
        if cls.client is None:
            cls.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        return cls.client

    @staticmethod
    async def send_otp(phone_number: str) -> bool:
        """
        Generate a 6-digit OTP, store it in Supabase, and send via Twilio.
        """
        try:
            # Generate 6-digit OTP
            otp_code = str(random.randint(100000, 999999))
            expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()

            # Store in Supabase
            # We use the public.otp_verifications table
            data = {
                "phone_number": phone_number,
                "otp_code": otp_code,
                "expires_at": expires_at,
                "verified": False
            }
            
            # Use SupabaseManager to insert (assuming it handles inserts via execute_query)
            result = await SupabaseManager.execute_query(
                table="otp_verifications",
                operation="insert",
                data=data
            )

            if not result.get("success"):
                logger.error(f"Failed to store OTP in database: {result.get('error')}")
                return False

            # Send via Twilio
            client = SmsService.get_client()
            message = client.messages.create(
                body=f"Your LankaPass verification code is: {otp_code}. It will expire in 10 minutes.",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            
            logger.info(f"OTP sent to {phone_number}. Message SID: {message.sid}")
            return True

        except Exception as e:
            logger.error(f"Error sending OTP: {str(e)}")
            return False

    @staticmethod
    async def verify_otp(phone_number: str, otp_code: str) -> bool:
        """
        Verify the OTP from Supabase.
        """
        try:
            # Fetch the latest unverified OTP for this phone number
            result = await SupabaseManager.execute_query(
                table="otp_verifications",
                operation="select",
                filters={
                    "phone_number": phone_number,
                    "otp_code": otp_code,
                    "verified": False
                }
            )

            if not result.get("success") or not result.get("data"):
                return False

            # Check expiration
            otp_data = result["data"][0] if isinstance(result["data"], list) else result["data"]
            expires_at = datetime.fromisoformat(otp_data["expires_at"].replace("Z", "+00:00"))
            
            if datetime.now(expires_at.tzinfo) > expires_at:
                logger.warning(f"OTP for {phone_number} expired.")
                return False

            # Mark as verified
            update_result = await SupabaseManager.execute_query(
                table="otp_verifications",
                operation="update",
                data={"verified": True},
                filters={"id": otp_data["id"]}
            )

            return update_result.get("success", False)

        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            return False
