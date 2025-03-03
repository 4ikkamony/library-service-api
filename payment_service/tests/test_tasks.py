from django.contrib.auth import get_user_model
from django.test import TestCase
from unittest.mock import patch, Mock
from payment_service.tasks import expire_payments
from payment_service.models import Payment
from borrowing_service.models import Borrowing
from book_service.models import Book
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class ExpirePaymentsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            email="testuser@example.com",
            password="testpass123"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover=Book.CoverType.HARD,
            inventory=10,
            daily_fee=1.50
        )
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=datetime.now().date(),
            expected_return_date=datetime.now().date() + timedelta(days=7)
        )
        self.expired_payment = Payment.objects.create(
            borrowing=self.borrowing,
            session_url="https://example.com/session",
            session_id="sess_123456",
            session_expires_at=datetime.now() - timedelta(hours=1),
            money_to_pay=10.99,
            status=Payment.Status.PENDING,
            type=Payment.Type.PAYMENT
        )
        self.active_payment = Payment.objects.create(
            borrowing=self.borrowing,
            session_url="https://example.com/session2",
            session_id="sess_789012",
            session_expires_at=datetime.now() + timedelta(hours=1),
            # Активная сессия
            money_to_pay=5.99,
            status=Payment.Status.PENDING,
            type=Payment.Type.FINE
        )
        self.mock_expired_sessions = Mock()
        self.patcher_expired_sessions = patch(
            "payment_service.tasks.expired_sessions",
            new=self.mock_expired_sessions
        )
        self.patcher_expired_sessions.start()

    def tearDown(self):
        if hasattr(self, "patcher_expired_sessions"):
            self.patcher_expired_sessions.stop()

    def test_expire_payments_success(self):
        self.mock_expired_sessions.return_value = (
            datetime.now().date(),
            Payment.objects.filter(id=self.expired_payment.id)
        )

        try:
            result = expire_payments()
        except Exception as e:
            self.fail(f"Function raised unexpected exception: {str(e)}")

        self.assertIsNone(result)

        self.expired_payment.refresh_from_db()
        self.assertEqual(self.expired_payment.status, Payment.Status.EXPIRED)

        self.active_payment.refresh_from_db()
        self.assertEqual(self.active_payment.status, Payment.Status.PENDING)

        self.mock_expired_sessions.assert_called_once()

    def test_expire_payments_no_expired(self):
        self.mock_expired_sessions.return_value = (
            datetime.now().date(),
            Payment.objects.none()
        )

        try:
            result = expire_payments()
        except Exception as e:
            self.fail(f"Function raised unexpected exception: {str(e)}")

        self.assertIsNone(result)

        self.expired_payment.refresh_from_db()
        self.assertEqual(self.expired_payment.status, Payment.Status.PENDING)
        self.active_payment.refresh_from_db()
        self.assertEqual(self.active_payment.status, Payment.Status.PENDING)

        self.mock_expired_sessions.assert_called_once()

    def test_expire_payments_database_error(self):
        self.mock_expired_sessions.side_effect = Exception(
            "Database connection failed"
        )

        with self.assertRaises(Exception) as context:
            expire_payments()

        self.assertEqual(
            str(context.exception),
            "Database connection failed"
        )

        self.expired_payment.refresh_from_db()
        self.assertEqual(self.expired_payment.status, Payment.Status.PENDING)
        self.active_payment.refresh_from_db()
        self.assertEqual(self.active_payment.status, Payment.Status.PENDING)

        self.mock_expired_sessions.assert_called_once()
