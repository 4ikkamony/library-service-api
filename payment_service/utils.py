from datetime import datetime

from django.db.models import QuerySet
from django.utils import timezone

from payment_service.models import Payment


def expired_sessions() -> tuple[datetime, QuerySet]:
    current_time = timezone.now()
    return (
        current_time,
        Payment.objects.filter(
        session_expires_at__lt=current_time,
        status=Payment.Status.PENDING
        )
    )
