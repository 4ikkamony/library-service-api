from django.core.exceptions import ValidationError
from django.db import models


class Book(models.Model):
    class CoverType(models.TextChoices):
        HARD = "hard", "Hard Cover"
        SOFT = "soft", "Soft Cover"

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(max_length=10, choices=CoverType.choices)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} by {self.author}"

    def clean(self):
        if self.daily_fee <= 0:
            raise ValidationError("Daily fee has to be greater than 0.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
