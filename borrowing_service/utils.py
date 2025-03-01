from datetime import date

from django.db.models import QuerySet
from django.utils import timezone

from borrowing_service.models import Borrowing


def today_overdue_borrowings() -> (date, QuerySet):
    today = timezone.now().date()
    overdue_borrowings = Borrowing.objects.filter(
        actual_return_date__isnull=True, expected_return_date__lte=today
    ).select_related("user", "book")

    return today, overdue_borrowings
