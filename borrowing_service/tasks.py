import logging

from celery import shared_task

from borrowing_service.models import Borrowing
from borrowing_service.utils import today_overdue_borrowings
from notifications_service.utils import send_notification, task_handler

# Used for Celery logging via:
# celery -A core.celery_config worker -l info
# Can be used in core/settings.py if needed
logger = logging.getLogger(__name__)


@shared_task
@task_handler
def notify_new_borrowing(self, borrowing_id):
    borrowing = Borrowing.objects.get(id=borrowing_id)
    message = (
        f"New Borrowing Created!\n"
        f"Borrowing ID: {borrowing.id}\n"
        f"User: {borrowing.user.email}\n"
        f"Book: {borrowing.book.title}\n"
        f"Borrow Date: {borrowing.borrow_date}\n"
        f"Expected Return Date: {borrowing.expected_return_date}"
    )
    send_notification(message)
    logger.info(f"Notification sent for new borrowing {borrowing.id}")


# If is needed to be moved to another service
# change in core/settings.py CELERY_BEAT_SCHEDULE
# 'task': 'borrowing_service.tasks.check_overdue_borrowings',
# with your service name and function name if it was changed!
@shared_task
@task_handler
def check_overdue_borrowings(self):
    today, overdue_borrowings = today_overdue_borrowings()
    if not overdue_borrowings.exists():
        send_notification("No borrowings overdue today!")
        logger.info("No overdue borrowings found, notification sent")
        return

    overdue_list = [
        (
            f"- Borrowing ID: {borrowing.id}\n"
            f"  User: {borrowing.user.email}\n"
            f"  Book: {borrowing.book.title}\n"
            f"  Expected Return Date: {borrowing.expected_return_date}\n"
            f"  Days Overdue: {(today - borrowing.expected_return_date).days}"
        )
        for borrowing in overdue_borrowings
    ]
    message = "Overdue Borrowings Alert!\n\n" + "\n\n".join(overdue_list)
    send_notification(message)
    logger.info(
        f"Notification sent for {overdue_borrowings.count()} overdue borrowings"
    )
