import datetime
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from book_service.models import Book
from payment_service.models import Payment
from borrowing_service.models import Borrowing
from payment_service.serializers import PaymentSerializer


class PaymentSerializerTest(TestCase):
    def setUp(self):
        self.book = Book.objects.create(
            title="Test Book", inventory=5, daily_fee=Decimal("1.50")
        )

        User = get_user_model()
        self.user = User.objects.create(email="testuser@mail.com")

        self.borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            expected_return_date=timezone.now().date() + datetime.timedelta(days=7),
        )

        self.payment = Payment.objects.create(
            borrowing=self.borrowing,
            session_url="https://example.com",
            session_id="12345",
            session_expires_at=timezone.now() + datetime.timedelta(days=1),
            money_to_pay=Decimal("10.00"),
            status=Payment.Status.PENDING,
            type=Payment.Type.PAYMENT,
        )

    def test_valid_serializer(self):
        data = {
            "borrowing": self.borrowing.id,
            "session_url": "https://example.com/session",
            "session_id": "xyz789",
            "session_expires_at": timezone.now() + datetime.timedelta(days=1),
            "money_to_pay": Decimal("100.00"),
            "status": Payment.Status.PAID,
            "type": Payment.Type.FINE,
        }
        serializer = PaymentSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_read_only_fields(self):
        serializer = PaymentSerializer(instance=self.payment)
        self.assertEqual(serializer.data["status"], Payment.Status.PENDING)
        self.assertEqual(serializer.data["type"], Payment.Type.PAYMENT)
