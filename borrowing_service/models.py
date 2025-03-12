from django.db import models
from django.conf import settings
from django.utils import timezone

from book_service.models import Book
from borrowing_service.validators import validate_borrowing


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowings")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="borrowings"
    )

    def clean(self):
        validate_borrowing(self)

    def save(self, *args, **kwargs):
        self.clean()
        if not self.pk:
            self.book.inventory -= 1
            self.book.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"Borrowing {self.book} by {self.user} on {self.borrow_date}. "
            f"Expected return date {self.expected_return_date}"
        )

    class Meta:
        ordering = ["-borrow_date"]
