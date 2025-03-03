from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta


from borrowing_service.models import Borrowing
from book_service.models import Book
from payment_service.models import Payment
from borrowing_service.serializers import (
    BorrowingCreateSerializer,
    BorrowingDetailSerializer,
    BorrowingReturnSerializer,
)

user = get_user_model()


class BorrowingSerializerTest(TestCase):
    def setUp(self):
        self.user = user.objects.create_user(
            email="testuser@test.com",
            first_name="Test",
            last_name="User",
            password="password",
        )
        self.book = Book.objects.create(
            title="Test Book", author="Test Author", daily_fee=10, inventory=5
        )
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=timezone.now().date() + timedelta(days=7),
        )

    def test_borrowing_create_success(self):
        data = {
            "book": self.book.id,
            "expected_return_date": timezone.now().date() + timedelta(days=7),
        }
        serializer = BorrowingCreateSerializer(
            data=data, context={"request": self.mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_borrowing_create_with_pending_payment(self):
        Payment.objects.create(
            borrowing=self.borrowing,
            status=Payment.Status.PENDING,
            money_to_pay=100,
        )
        data = {
            "book": self.book.id,
            "expected_return_date": timezone.now().date() + timedelta(days=7),
        }
        serializer = BorrowingCreateSerializer(
            data=data, context={"request": self.mock_request(user=self.borrowing.user)}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "You cannot borrow new books with pending payment.", str(serializer.errors)
        )

    def test_borrowing_create_book_out_of_stock(self):
        self.book.inventory = 0
        self.book.save()
        data = {
            "book": self.book.id,
            "expected_return_date": timezone.now().date() + timedelta(days=7),
        }
        serializer = BorrowingCreateSerializer(
            data=data, context={"request": self.mock_request()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("Selected book is out of stock.", str(serializer.errors))

    def test_borrowing_create_book_in_stock(self):
        data = {
            "book": self.book.id,
            "expected_return_date": timezone.now().date() + timedelta(days=7),
        }
        serializer = BorrowingCreateSerializer(
            data=data, context={"request": self.mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_borrowing_create_invalid_return_date(self):
        data = {
            "book": self.book.id,
            "expected_return_date": timezone.now().date() - timedelta(days=1),
        }
        serializer = BorrowingCreateSerializer(
            data=data, context={"request": self.mock_request()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "Expected return date cannot be earlier than borrow date.",
            str(serializer.errors),
        )

    def test_borrowing_detail_serializer(self):
        serializer = BorrowingDetailSerializer(instance=self.borrowing)
        data = serializer.data
        self.assertEqual(data["id"], self.borrowing.id)
        self.assertEqual(data["book"]["id"], self.book.id)
        self.assertEqual(data["user"]["email"], self.user.email)

    def test_borrowing_return_serializer(self):
        self.borrowing.actual_return_date = timezone.now().date()
        self.borrowing.save()

        serializer = BorrowingReturnSerializer(instance=self.borrowing)
        data = serializer.data
        self.assertIn("actual_return_date", data)
        self.assertEqual(data["actual_return_date"], timezone.now().date().isoformat())

    def mock_request(self, user=None):
        request = Mock()
        if user is None:
            user = get_user_model().objects.create_user(
                email="testuser@example.com", password="password123"
            )
        request.user = user
        return request
