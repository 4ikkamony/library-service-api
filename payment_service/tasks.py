import logging
from datetime import datetime

from celery import shared_task

from notifications_service.utils import (
    send_telegram_message,
    task_handler,
    send_notification,
)
from payment_service.models import Payment
from payment_service.utils import expired_sessions

logger = logging.getLogger(__name__)


def is_payment_paid(payment):
    return payment.status == Payment.Status.PAID


@shared_task
@task_handler
def expire_payments(self):
    """
    This task finds Payments with expired Stripe Sessions
    and sets their status to expired
    """
    now, payments_to_expire = expired_sessions()
    count = payments_to_expire.count()
    logger.info(f"Found {count} expired payment sessions")
    if payments_to_expire.exists():
        payments_to_expire.update(status=Payment.Status.EXPIRED)
        logger.info(f"Set {count} Payments as 'expired'")


@shared_task
@task_handler
def notify_new_payment(self, payment_id):
    """
    Task to notify successful Payment
    """
    payment = Payment.objects.get(id=payment_id)
    message = (
        f"New Payment Created!\n"
        f"Payment ID: {payment.id}\n"
        f"Borrowing ID: {payment.borrowing.id}\n"
        f"User: {payment.borrowing.user.email}\n"
        f"Book: {payment.borrowing.book.title}\n"
        f"Amount to Pay: ${payment.money_to_pay}\n"
        f"Type: {payment.type}\n"
        f"Status: {payment.status}\n"
    )
    send_notification(message)


@shared_task
@task_handler
def notify_successful_payment(self, payment_id):
    """
    Task to notify about a successful payment (status 'PAID').
    """
    payment = Payment.objects.get(id=payment_id)
    if not is_payment_paid(payment):
        logger.warning(
            f"Payment {payment_id} status is not 'PAID', skipping notification"
        )
        return
    message = (
        f"Payment Successfully Completed!\n"
        f"Payment ID: {payment.id}\n"
        f"Borrowing ID: {payment.borrowing.id}\n"
        f"User: {payment.borrowing.user.email}\n"
        f"Book: {payment.borrowing.book.title}\n"
        f"Amount Paid: ${payment.money_to_pay}\n"
        f"Type: {payment.type}\n"
        f"Status: {payment.status}\n"
        f"Payment Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    send_notification(message)
