import logging
from datetime import date, timedelta
from celery import shared_task

from notifications_service.utils import send_telegram_message

# Used for Celery logging via:
# celery -A core.celery_config worker -l info
# Can be used in core/settings.py if needed
logger = logging.getLogger(__name__)


@shared_task(max_retries=3, bind=True)
def notify_new_borrowing(self, borrowing_id, user_email, book_title) -> None:
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


class MockBorrowing:
    def __init__(self, id, user_email, book_title, expected_return_date):
        self.id = id
        self.user = type("User", (), {"email": user_email})()
        self.book = type("Book", (), {"title": book_title})()
        self.expected_return_date = expected_return_date
        self.actual_return_date = None


@shared_task
def check_overdue_borrowings():
    today = date.today()
    overdue_borrowings = [
        MockBorrowing(
            1,
            "user@example.com",
            "Test Book",
            today - timedelta(days=2)
        ),
    ]

    if not overdue_borrowings:
        message = "No borrowings overdue today!"
        success = send_telegram_message(message)
        if not success:
            logger.error("Failed to send 'no overdue borrowings' notification")
            raise Exception("Failed to send Telegram notification")
        logger.info("No overdue borrowings found, notification sent")
        return

    for borrowing in overdue_borrowings:
        message = (
            f"Overdue Borrowing Alert! Hello from Beats!\n"
            f"Borrowing ID: {borrowing.id}\n"
            f"User: {borrowing.user.email}\n"
            f"Book: {borrowing.book.title}\n"
            f"Expected Return Date: {borrowing.expected_return_date}\n"
            f"Days Overdue: {(today - borrowing.expected_return_date).days}"
        )
        success = send_telegram_message(message)
        if not success:
            logger.error(
                f"Failed to send notification for borrowing {borrowing.id}"
            )
            raise Exception("Failed to send Telegram notification")
        logger.info(f"Notification sent for overdue borrowing {borrowing.id}")

    logger.info(f"Checked {len(overdue_borrowings)} overdue borrowings")
