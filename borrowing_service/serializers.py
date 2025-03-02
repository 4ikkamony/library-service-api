from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from borrowing_service.models import Borrowing
from book_service.models import Book
from payment_service.models import Payment
from payment_service.utils import create_payment_session
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

    def validate(self, data):
        user = self.context["request"].user
        pending_payments = Payment.objects.filter(
            borrowing__user=user, status=Payment.Status.PENDING
        )

        if pending_payments.exists():
            raise serializers.ValidationError(
                "You cannot borrow new books with pending payment."
            )

        book = data.get("book")
        if book and book.inventory <= 0:
            raise serializers.ValidationError("Selected book is out of stock.")

        expected_return_date = data.get("expected_return_date")
        today = timezone.now().date()
        if expected_return_date and expected_return_date < today:
            raise serializers.ValidationError(
                "Expected return date cannot be earlier than borrow date."
            )

        return data

    def create(self, validated_data):
        request = self.context["request"]
        with transaction.atomic():
            borrowing = Borrowing.objects.create(**validated_data)
            create_payment_session(borrowing, request, Payment.Type.PAYMENT)

        return borrowing


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
    actual_return_date = serializers.DateField(default=timezone.now, read_only=True)

    class Meta:
        model = Borrowing
        fields = ("id", "actual_return_date")
