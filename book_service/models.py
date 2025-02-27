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
