from twilio.rest import Client
from src.core.config import config
import logging

logger = logging.getLogger(__name__)

class WhatsAppAdapter:
    def __init__(self):
        self.account_sid = config.TWILIO_ACCOUNT_SID
        self.auth_token = config.TWILIO_AUTH_TOKEN
        self.from_number = config.TWILIO_WHATSAPP_NUMBER
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
            logger.warning("Twilio credentials not set. WhatsAppAdapter disabled.")

    def send_message(self, to: str, text: str):
        """
        Sends a WhatsApp message using Twilio.
        Args:
            to (str): Recipient phone number in E.164 format (e.g., +14155552671).
            text (str): The body of the message.
        """
        if not self.client:
            logger.info(f"Mock Message (Twilio not configured) to {to}: {text}")
            return

        # Ensure 'to' number has whatsapp: prefix if not present
        if not to.startswith("whatsapp:"):
            target = f"whatsapp:{to}"
        else:
            target = to

        # Ensure 'from' number has whatsapp: prefix
        if not self.from_number.startswith("whatsapp:"):
            sender = f"whatsapp:{self.from_number}"
        else:
            sender = self.from_number

        try:
            message = self.client.messages.create(
                from_=sender,
                body=text,
                to=target
            )
            logger.info(f"Message sent to {to}. SID: {message.sid}")
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message via Twilio: {e}")
