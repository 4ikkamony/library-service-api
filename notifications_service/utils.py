import os
from functools import wraps

import requests
import logging
from django.conf import settings

#  all logs are going through StreamHandler in console when Celery is running
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


def task_handler(max_retries=3, countdown=60):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                logger.info(
                    f"Processing task {func.__name__} with args={args}, kwargs={kwargs}"
                )
                result = func(self, *args, **kwargs)
                logger.info(f"Task {func.__name__} completed successfully")
                return result
            except Exception as exc:
                logger.error(f"Error in {func.__name__}: {str(exc)}")
                if isinstance(exc, self.retry.__class__):
                    raise exc
                raise self.retry(exc=exc, max_retries=max_retries, countdown=countdown)

        return wrapper

    return decorator


def send_notification(message):
    success = send_telegram_message(message)
    if not success:
        raise Exception("Failed to send Telegram notification")
    return success
