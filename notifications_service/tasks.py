from celery import shared_task
from .utils import send_telegram_message


# TODO: remove with notify new borrowing
@shared_task
def send_test_telegram_message():
    """Test task for sending a message to Telegram."""
    message = "Test notification!"
    success = send_telegram_message(message)
    if not success:
        raise Exception("Failed to send test Telegram message")
