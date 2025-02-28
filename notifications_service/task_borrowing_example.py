import logging

# Used for Celery logging via:
# celery -A core.celery_config worker -l info
# Can be used in core/settings.py if needed
logger = logging.getLogger(__name__)

from celery import shared_task
from .utils import send_telegram_message


@shared_task(max_retries=3)
def notify_new_borrowing(borrowing_id, user_email, book_title):
    try:
        logger.info(
            f"Processing notify_new_borrowing for borrowing_id={borrowing_id}"
        )
        message = (
            f"New Borrowing Created!\n"
            f"Borrowing ID: {borrowing_id}\n"
            f"User: {user_email}\n"
            f"Book: {book_title}"
        )
        success = send_telegram_message(message)
        if not success:
            logger.error("Failed to send Telegram notification")
            raise Exception("Failed to send Telegram notification")
    except Exception as exc:
        logger.error(f"Error in notify_new_borrowing: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)
