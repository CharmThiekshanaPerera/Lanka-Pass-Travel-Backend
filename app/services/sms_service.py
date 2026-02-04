import random
import logging
from datetime import datetime, timedelta
from app.config import settings
from app.database.supabase_client import SupabaseManager
import httpx

logger = logging.getLogger(__name__)

class SmsService:
    @staticmethod
    async def send_otp(phone_number: str) -> bool:
        """
        Generate a 6-digit OTP, store it in Supabase, and send via Text.lk.
        """
        try:
            # Generate 6-digit OTP
            otp_code = str(random.randint(100000, 999999))
            expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()

            # Store in Supabase
            data = {
                "phone_number": phone_number,
                "otp_code": otp_code,
                "expires_at": expires_at,
                "verified": False
            }
            
            result = await SupabaseManager.execute_query(
                table="otp_verifications",
                operation="insert",
                data=data
            )

            if not result.get("success"):
                logger.error(f"Failed to store OTP in database: {result.get('error')}")
                return False

            # Send via Text.lk
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://app.text.lk/api/v3/sms/send",
                    headers={
                        "Authorization": f"Bearer {settings.TEXT_LK_API_KEY}",
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    json={
                        "recipient": phone_number,
                        "sender_id": settings.TEXT_LK_SENDER_ID,
                        "type": "plain",
                        "message": f"Your LankaPass verification code is: {otp_code}. It will expire in 10 minutes."
                    },
                    timeout=10.0
                )

                if response.status_code == 200:
                    logger.info(f"OTP sent to {phone_number} via Text.lk. Response: {response.text}")
                    return True
                else:
                    logger.error(f"Text.lk API error: {response.status_code} - {response.text}")
                    return False

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
            # We sort by created_at desc to get the most recent one
            # Note: SupabaseManager.execute_query might need custom order handling if it supports it
            # But usually we filter by phone and code and verified=false
            result = await SupabaseManager.execute_query(
                table="otp_verifications",
                operation="select",
                filters={
                    "phone_number": phone_number,
                    "otp_code": otp_code,
                    "verified": False
                }
            )

            if not result.get("success") or not result.get("data") or len(result["data"]) == 0:
                logger.warning(f"No matching unverified OTP found for {phone_number}")
                return False

            # Check expiration
            otp_data = result["data"][0] if isinstance(result["data"], list) else result["data"]
            expires_at_str = otp_data["expires_at"]
            
            # Handle different timestamp formats from Supabase
            if "T" in expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            else:
                expires_at = datetime.fromisoformat(expires_at_str + "+00:00")

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
