import random
import logging
from datetime import datetime, timedelta
from app.config import settings
from app.database.supabase_client import SupabaseManager
import httpx

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    async def send_otp(email: str) -> bool:
        """
        Generate a 6-digit OTP, store it in Supabase, and send via SendGrid.
        """
        try:
            # Generate 6-digit OTP
            otp_code = str(random.randint(100000, 999999))
            expires_at = (datetime.now() + timedelta(minutes=15)).isoformat()

            # Store in Supabase
            data = {
                "email": email,
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
                logger.error(f"Failed to store Email OTP in database: {result.get('error')}")
                return False

            # Check if SendGrid is configured
            if not settings.SENDGRID_API_KEY or not settings.SENDGRID_FROM_EMAIL:
                logger.warning("SendGrid is not configured. OTP stored but not sent.")
                # For development/testing, we might want to return True if the database part worked
                # but let's be strict for now.
                return False

            # Send via SendGrid API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "personalizations": [
                            {
                                "to": [{"email": email}],
                                "subject": "Your LankaPass Verification Code"
                            }
                        ],
                        "from": {"email": settings.SENDGRID_FROM_EMAIL, "name": "LankaPass Travel"},
                        "content": [
                            {
                                "type": "text/plain",
                                "value": f"Your LankaPass verification code is: {otp_code}. It will expire in 15 minutes."
                            },
                            {
                                "type": "text/html",
                                "value": f"""
                                <div style="font-family: sans-serif; padding: 20px; border: 1px solid #eee; border-radius: 10px; max-width: 600px; margin: auto;">
                                    <h2 style="color: #0d9488;">LankaPass Account Verification</h2>
                                    <p>Thank you for joining LankaPass Travel. Please use the following code to verify your email address:</p>
                                    <div style="background: #f3f4f6; padding: 15px; text-align: center; border-radius: 8px; font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #fbbf24; margin: 20px 0;">
                                        {otp_code}
                                    </div>
                                    <p style="color: #6b7280; font-size: 14px;">This code will expire in 15 minutes.</p>
                                    <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;" />
                                    <p style="color: #9ca3af; font-size: 12px; text-align: center;">This is an automated message, please do not reply.</p>
                                </div>
                                """
                            }
                        ]
                    },
                    timeout=10.0
                )

                if response.status_code in [200, 201, 202]:
                    logger.info(f"Email OTP sent to {email} via SendGrid.")
                    return True
                else:
                    logger.error(f"SendGrid API error: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error sending Email OTP: {str(e)}")
            return False

    @staticmethod
    async def verify_otp(email: str, otp_code: str) -> bool:
        """
        Verify the Email OTP from Supabase.
        """
        try:
            # Fetch the latest unverified OTP for this email
            result = await SupabaseManager.execute_query(
                table="otp_verifications",
                operation="select",
                filters={
                    "email": email,
                    "otp_code": otp_code,
                    "verified": False
                }
            )

            if not result.get("success") or not result.get("data") or len(result["data"]) == 0:
                logger.warning(f"No matching unverified Email OTP found for {email}")
                return False

            # Check expiration
            otp_data = result["data"][0] if isinstance(result["data"], list) else result["data"]
            expires_at_str = otp_data["expires_at"]
            
            if "T" in expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            else:
                expires_at = datetime.fromisoformat(expires_at_str + "+00:00")

            if datetime.now(expires_at.tzinfo) > expires_at:
                logger.warning(f"Email OTP for {email} expired.")
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
            logger.error(f"Error verifying Email OTP: {str(e)}")
            return False
