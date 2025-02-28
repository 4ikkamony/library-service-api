import os
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_telegram_message(message: str) -> bool:
    """Send a message to Telegram chat."""
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            logger.error(f"Telegram API error: {response.text}")
            return False
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {str(e)}")
        return False
