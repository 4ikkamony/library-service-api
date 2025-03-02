import datetime

from django.db import models
from django.utils import timezone

from borrowing_service.models import Borrowing


def datetime_from_timestamp(timestamp: int):
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        EXPIRED = "expired", "Expired"

    class Type(models.TextChoices):
        PAYMENT = "payment", "Payment"
        FINE = "fine", "Fine"

    borrowing = models.ForeignKey(
        Borrowing, on_delete=models.CASCADE, related_name="payment"
    )
    session_url = models.URLField(max_length=400)
    session_id = models.CharField(max_length=255)
    session_expires_at = models.DateTimeField(default=timezone.now)
    money_to_pay = models.DecimalField(max_digits=6, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    type = models.CharField(max_length=10, choices=Type.choices, default=Type.PAYMENT)
