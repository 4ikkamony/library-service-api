import logging

from celery import shared_task

from borrowing_service.models import Borrowing
from borrowing_service.utils import today_overdue_borrowings
from notifications_service.utils import send_telegram_message

# Used for Celery logging via:
# celery -A core.celery_config worker -l info
# Can be used in core/settings.py if needed
logger = logging.getLogger(__name__)


@shared_task(max_retries=3, bind=True)
def notify_new_borrowing(self, borrowing_id) -> None:
    try:
        logger.info(f"Processing notify_new_borrowing for borrowing_id={borrowing_id}")
        borrowing = Borrowing.objects.get(id=borrowing_id)

        message = (
            f"New Borrowing Created!\n"
            f"Borrowing ID: {borrowing.id}\n"
            f"User: {borrowing.user.email}\n"
            f"Book: {borrowing.book.title}\n"
            f"Borrow Date: {borrowing.borrow_date}\n"
            f"Expected Return Date: {borrowing.expected_return_date}"
        )

        success = send_telegram_message(message)
        if not success:
            logger.error(f"Failed to send notification for borrowing {borrowing.id}")
            raise Exception("Failed to send Telegram notification")
        logger.info(f"Notification sent for new borrowing {borrowing.id}")
    except Borrowing.DoesNotExist:
        logger.error(f"Borrowing with ID {borrowing_id} not found")
        raise Exception(f"Borrowing with ID {borrowing_id} not found")
    except Exception as exc:
        logger.error(f"Error in notify_new_borrowing: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


# If is needed to be moved to another service
# change in core/settings.py CELERY_BEAT_SCHEDULE
# 'task': 'borrowing_service.tasks.check_overdue_borrowings',
# with your service name and function name if it was changed!
@shared_task(bind=True, max_retries=3)
def check_overdue_borrowings(self):
    today, overdue_borrowings = today_overdue_borrowings()

    try:
        if not overdue_borrowings.exists():
            message = "No borrowings overdue today!"
            success = send_telegram_message(message)
            if not success:
                logger.error("Failed to send 'no overdue borrowings' notification")
                raise Exception("Failed to send Telegram notification")
            logger.info("No overdue borrowings found, notification sent")
            return

        overdue_list = []
        for borrowing in overdue_borrowings:
            overdue_info = (
                f"- Borrowing ID: {borrowing.id}\n"
                f"  User: {borrowing.user.email}\n"
                f"  Book: {borrowing.book.title}\n"
                f"  Expected Return Date: {borrowing.expected_return_date}\n"
                f"  Days Overdue: {(today - borrowing.expected_return_date).days}"
            )
            overdue_list.append(overdue_info)

        message = "Overdue Borrowings Alert!\n\n" + "\n\n".join(overdue_list)

        success = send_telegram_message(message)
        if not success:
            logger.error("Failed to send overdue borrowings notification")
            raise Exception("Failed to send Telegram notification")

        logger.info(
            f"Notification sent for {overdue_borrowings.count()} overdue borrowings"
        )
        logger.info(f"Checked {overdue_borrowings.count()} overdue borrowings")
    except Exception as exc:
        logger.error(f"Error in check_overdue_borrowings: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)
