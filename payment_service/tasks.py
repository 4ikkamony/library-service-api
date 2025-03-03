import logging

from celery import shared_task

from notifications_service.utils import send_telegram_message
from payment_service.models import Payment
from payment_service.utils import expired_sessions

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def expire_payments(self):
    """
    This task finds Payments with expired Stripe Sessions
    and sets their status to expired
    """
    now, payments_to_expire = expired_sessions()
    count = payments_to_expire.count()

    logger.info(f"Found {count} expired payment sessions")

    try:
        if payments_to_expire.exists():
            payments_to_expire.update(status=Payment.Status.EXPIRED)
            logger.info(f"Set {count} Payments as 'expired'")
    except Exception as exc:
        logger.error(f"Error in expire_payments: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(max_retries=3, bind=True)
def notify_new_payment(self, payment_id):
    """
    Task to notify successful Payment
    """
    try:
        logger.info(f"Processing notify_new_payment for payment_id={payment_id}")
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

        success = send_telegram_message(message)
        if not success:
            logger.error(f"Failed to send notification for payment {payment.id}")
            raise Exception("Failed to send Telegram notification")
        logger.info(f"Notification sent for new payment {payment.id}")
    except Payment.DoesNotExist:
        logger.error(f"Payment with ID {payment_id} not found")
        raise Exception(f"Payment with ID {payment_id} not found")
    except Exception as exc:
        logger.error(f"Error in notify_new_payment: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)
