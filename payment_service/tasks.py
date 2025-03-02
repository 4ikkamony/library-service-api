import logging

from celery import shared_task

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
