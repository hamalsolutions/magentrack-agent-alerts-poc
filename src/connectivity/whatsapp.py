import logging
import requests
from src.core.config import config

logger = logging.getLogger(__name__)

class WhatsAppAdapter:
    def __init__(self):
        self.api_url = f"https://graph.facebook.com/v17.0/{config.WHATSAPP_PHONE_ID}/messages"
        self.headers = {
            "Authorization": f"Bearer {config.WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json"
        }

    def send_message(self, to: str, text: str):
        """
        Sends a text message to the specified phone number using WhatsApp Cloud API.
        """
        if not config.WHATSAPP_API_TOKEN:
            logger.warning("WhatsApp API Token not set. Skipping message send.")
            logger.info(f"Mock Message to {to}: {text}")
            return

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Message sent to {to}: {response.json()}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
