from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from borrowing_service.models import Borrowing
from book_service.models import Book
from user.models import User


class BorrowingUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")


class BorrowingBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover", "daily_fee")


class BorrowingCreateSerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "expected_return_date",
            "book",
        )

    def validate_book(self, value):
        if value.inventory <= 0:
            raise serializers.ValidationError("Selected book is out of stock.")
        return value

    def validate_borrowing_date(self, data):
        today = timezone.now().date()
        borrow_date = today

        if data["expected_return_date"] < borrow_date:
            raise serializers.ValidationError(
                "Expected return date cannot be earlier than borrow date."
            )

    def create(self, validated_data):
        with transaction.atomic():
            book = validated_data["book"]

            book.inventory -= 1
            book.save()

            return super().create(validated_data)


class BorrowingDetailSerializer(serializers.ModelSerializer):
    book = BorrowingBookSerializer(read_only=True)
    user = BorrowingUserSerializer(read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "user",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
        )


class BorrowingListSerializer(serializers.ModelSerializer):
    book = BorrowingBookSerializer(read_only=True)
    user = BorrowingUserSerializer(read_only=True)

    class Meta:
        model = Borrowing
        fields = ("id", "user", "book", "expected_return_date", "actual_return_date")


class BorrowingReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "actual_return_date")
