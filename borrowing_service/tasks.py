import logging

from celery import Task, shared_task

from borrowing_service.utils import today_overdue_borrowings
from notifications_service.utils import send_telegram_message


# Used for Celery logging via:
# celery -A core.celery_config worker -l info
# Can be used in core/settings.py if needed

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def notify_overdue_borrowings(self):
    today, overdue_borrowings = today_overdue_borrowings()
    messages = []
    if overdue_borrowings:
        for borrowing in overdue_borrowings:
            messages.append(
                f"{today} Overdue Borrowing:\n"
                f"Borrowing ID: {borrowing.id}\n"
                f"User: {borrowing.user.email}\n"
                f"Book: {borrowing.book.title}"
            )
    else:
        messages.append(f"No borrowings overdue for {today}")

    for message in messages:
        try:
            logger.info(f"Processing notify_overdue_borrowings")
            success = send_telegram_message(message)
            if not success:
                logger.error("Failed to send Telegram notification")
                raise Exception("Failed to send Telegram notification")
        except Exception as exc:
            logger.error(f"Error in notify_new_borrowing: {str(exc)}")
            raise self.retry(exc=exc, countdown=60)
