from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings

from book_service.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowings")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="borrowings"
    )

    def clean(self):
        if self.book.inventory <= 0:
            raise ValidationError(
                "Selected book is out of stock."
            )

        if self.expected_return_date < self.borrow_date:
            raise ValidationError(
                "Expected return date is earlier than borrow date."
            )

        if self.actual_return_date and self.actual_return_date < self.borrow_date:
            raise ValidationError(
                "Actual return date cannot be earlier than borrow date."
            )

    def save(self, *args, **kwargs):
        self.clean()
        if not self.pk:
            self.book.inventory -= 1
            self.book.save()

        super().save(*args, **kwargs)
