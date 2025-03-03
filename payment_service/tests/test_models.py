from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

from django.test import TestCase

from django.contrib.auth import get_user_model

from book_service.models import Book
from borrowing_service.models import Borrowing
from payment_service.models import Payment

User = get_user_model()


class PaymentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com",
            password="testpass",
        )

        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover=Book.CoverType.HARD,
            inventory=5,
            daily_fee=1.00,
        )

        self.borrow_date = timezone.now().date()
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=self.borrow_date + timezone.timedelta(days=7),
        )

    def test_valid_money_to_pay(self):
        """Test that a payment with positive money_to_pay can be created"""
        payment = Payment(
            borrowing=self.borrowing,
            session_url="https://example.com/checkout",
            session_id="cs_test_123456789",
            session_expires_at=timezone.now() + timezone.timedelta(hours=1),
            money_to_pay=Decimal("25.50"),
            type=Payment.Type.PAYMENT,
        )

        payment.full_clean()
        payment.save()

        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(Payment.objects.first().money_to_pay, Decimal("25.50"))

    def test_negative_money_to_pay(self):
        """Test that a payment with negative money_to_pay raises a ValidationError"""
        payment = Payment(
            borrowing=self.borrowing,
            session_url="https://example.com/checkout",
            session_id="cs_test_123456789",
            session_expires_at=timezone.now() + timezone.timedelta(hours=1),
            money_to_pay=Decimal("-10.50"),
            type=Payment.Type.FINE,
        )

        with self.assertRaises(ValidationError):
            payment.full_clean()
            payment.save()

        self.assertEqual(Payment.objects.count(), 0)

    def test_zero_money_to_pay(self):
        """Test that a payment with zero money_to_pay raises a ValidationError"""
        payment = Payment(
            borrowing=self.borrowing,
            session_url="https://example.com/checkout",
            session_id="cs_test_123456789",
            session_expires_at=timezone.now() + timezone.timedelta(hours=1),
            money_to_pay=Decimal("0.00"),
            type=Payment.Type.PAYMENT,
        )

        with self.assertRaises(ValidationError):
            payment.full_clean()
            payment.save()

        self.assertEqual(Payment.objects.count(), 0)
