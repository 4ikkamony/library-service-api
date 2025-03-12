from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_borrowing(borrowing):
    if not borrowing.borrow_date:
        borrowing.borrow_date = timezone.now().date()

    if borrowing.book.inventory <= 0:
        raise ValidationError("Selected book is out of stock.")

    if borrowing.expected_return_date < borrowing.borrow_date:
        raise ValidationError("Expected return date is earlier than borrow date.")

    if borrowing.actual_return_date:
        if borrowing.actual_return_date < borrowing.borrow_date:
            raise ValidationError(
                "Actual return date cannot be earlier than borrow date."
            )
