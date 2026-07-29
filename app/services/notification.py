import os
import uuid
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("nexpire.notifications")

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TwilioClient = None
    TWILIO_AVAILABLE = False


class TwilioNotificationService:
    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
        self.sms_from = os.environ.get("TWILIO_SMS_FROM_NUMBER", "+10000000000")
        self.whatsapp_from = os.environ.get("TWILIO_WHATSAPP_FROM_NUMBER", "whatsapp:+10000000000")

        # Determine if we have real credentials or should run in Mock Mode
        is_placeholder = (
            not self.account_sid
            or "your_" in self.account_sid
            or not self.auth_token
            or "your_" in self.auth_token
            or not self.account_sid.startswith("AC")
        )

        self.mock_mode = (not TWILIO_AVAILABLE) or is_placeholder
        self.client = None

        if not self.mock_mode and TWILIO_AVAILABLE:
            try:
                self.client = TwilioClient(self.account_sid, self.auth_token)
            except Exception as e:
                logger.warning(f"Failed to initialize Twilio Client, falling back to mock mode: {e}")
                self.mock_mode = True

    def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        """Send an outbound SMS message via Twilio or Mock Mode."""
        if self.mock_mode:
            simulated_sid = f"SIM_SMS_{uuid.uuid4().hex[:12]}"
            logger.info(f"[MOCK SMS] To: {to_phone} | Msg: {message} | SID: {simulated_sid}")
            return {
                "status": "simulated",
                "message_sid": simulated_sid,
                "channel": "sms",
                "recipient": to_phone,
                "mock_mode": True,
            }

        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.sms_from,
                to=to_phone
            )
            return {
                "status": "sent",
                "message_sid": msg.sid,
                "channel": "sms",
                "recipient": to_phone,
                "mock_mode": False,
            }
        except Exception as e:
            logger.error(f"Error sending SMS to {to_phone}: {e}")
            # Fallback to mock/error handling
            return {
                "status": "error",
                "message_sid": f"ERR_{uuid.uuid4().hex[:8]}",
                "channel": "sms",
                "recipient": to_phone,
                "mock_mode": self.mock_mode,
                "error": str(e),
            }

    def send_whatsapp(self, to_phone: str, message: str) -> Dict[str, Any]:
        """Send an outbound WhatsApp message via Twilio or Mock Mode."""
        formatted_to = to_phone if to_phone.startswith("whatsapp:") else f"whatsapp:{to_phone}"
        formatted_from = self.whatsapp_from if self.whatsapp_from.startswith("whatsapp:") else f"whatsapp:{self.whatsapp_from}"

        if self.mock_mode:
            simulated_sid = f"SIM_WA_{uuid.uuid4().hex[:12]}"
            logger.info(f"[MOCK WHATSAPP] To: {formatted_to} | Msg: {message} | SID: {simulated_sid}")
            return {
                "status": "simulated",
                "message_sid": simulated_sid,
                "channel": "whatsapp",
                "recipient": formatted_to,
                "mock_mode": True,
            }

        try:
            msg = self.client.messages.create(
                body=message,
                from_=formatted_from,
                to=formatted_to
            )
            return {
                "status": "sent",
                "message_sid": msg.sid,
                "channel": "whatsapp",
                "recipient": formatted_to,
                "mock_mode": False,
            }
        except Exception as e:
            logger.error(f"Error sending WhatsApp to {formatted_to}: {e}")
            return {
                "status": "error",
                "message_sid": f"ERR_{uuid.uuid4().hex[:8]}",
                "channel": "whatsapp",
                "recipient": formatted_to,
                "mock_mode": self.mock_mode,
                "error": str(e),
            }

    def format_flash_sale_message(
        self,
        item_name: str,
        store_name: str,
        original_price: float,
        discounted_price: float,
        discount_percentage: float,
        claim_url: Optional[str] = None,
    ) -> str:
        """Format standardized flash sale notification body."""
        url_text = f"\nClaim now: {claim_url}" if claim_url else ""
        return (
            f"🚨 NEXPIRE FLASH SALE @ {store_name}!\n"
            f"{item_name} is now {discount_percentage:.0f}% OFF!\n"
            f"Was ${original_price:.2f} ➔ Now ${discounted_price:.2f}"
            f"{url_text}\n"
            f"Reply 'YES' to quickly reserve this deal!"
        )

    def send_flash_sale_alert(
        self,
        to_phone: str,
        item_name: str,
        store_name: str,
        original_price: float,
        discounted_price: float,
        discount_percentage: float,
        claim_url: Optional[str] = None,
        channel: str = "sms",
    ) -> Dict[str, Any]:
        """Format and dispatch a flash sale alert to recipient via specified channel."""
        body = self.format_flash_sale_message(
            item_name=item_name,
            store_name=store_name,
            original_price=original_price,
            discounted_price=discounted_price,
            discount_percentage=discount_percentage,
            claim_url=claim_url,
        )
        if channel.lower() == "whatsapp":
            return self.send_whatsapp(to_phone, body)
        return self.send_sms(to_phone, body)


_notification_service_instance = None


def get_notification_service() -> TwilioNotificationService:
    global _notification_service_instance
    if _notification_service_instance is None:
        _notification_service_instance = TwilioNotificationService()
    return _notification_service_instance
