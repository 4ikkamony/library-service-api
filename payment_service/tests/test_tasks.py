from django.contrib.auth import get_user_model
from django.test import TestCase
from unittest.mock import patch, Mock
from payment_service.tasks import (
    expire_payments,
    notify_new_payment,
    notify_successful_payment
)
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


class NotifyNewPaymentTestCase(TestCase):
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
        self.payment = Payment.objects.create(
            borrowing=self.borrowing,
            session_url="https://example.com/session",
            session_id="test_session_123",
            session_expires_at=datetime.now().date() + timedelta(days=1),
            money_to_pay=15.00,
            status=Payment.Status.PENDING,
            type=Payment.Type.PAYMENT
        )

        self.mock_send_telegram = Mock(return_value=True)
        self.patcher_send_telegram = patch(
            "payment_service.tasks.send_telegram_message",
            new=self.mock_send_telegram
        )
        self.patcher_send_telegram.start()

    def tearDown(self):
        self.patcher_send_telegram.stop()

    def test_notify_new_payment_success(self):
        try:
            result = notify_new_payment(self.payment.id)
        except Exception as e:
            self.fail(f"Function raised unexpected exception: {str(e)}")

        self.assertIsNone(result)

        expected_message = (
            "New Payment Created!\n"
            f"Payment ID: {self.payment.id}\n"
            f"Borrowing ID: {self.borrowing.id}\n"
            f"User: {self.user.email}\n"
            f"Book: {self.book.title}\n"
            f"Amount to Pay: ${self.payment.money_to_pay:.2f}\n"
            f"Type: {self.payment.type}\n"
            f"Status: {self.payment.status}\n"
        )
        self.mock_send_telegram.assert_called_once_with(expected_message)

    def test_notify_new_payment_not_found(self):
        non_existent_id = 999

        with self.assertRaises(Exception) as context:
            notify_new_payment(non_existent_id)

        self.assertEqual(
            str(context.exception),
            f"Payment with ID {non_existent_id} not found"
        )

        self.mock_send_telegram.assert_not_called()

    def test_notify_new_payment_telegram_failure(self):
        self.mock_send_telegram.return_value = False

        with self.assertRaises(Exception) as context:
            notify_new_payment(self.payment.id)

        self.assertEqual(
            str(context.exception),
            "Failed to send Telegram notification"
        )

        self.mock_send_telegram.assert_called_once()


class NotifySuccessfulPaymentTestCase(TestCase):
    fixed_date = datetime(2025, 3, 3).date()

    def setUp(self):
        self.user = User.objects.create(
            email="testuser@example.com",
            password="password123"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Author",
            inventory=30,
            daily_fee=5.00
        )
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=self.fixed_date,
            expected_return_date=self.fixed_date + timedelta(days=7)
        )
        self.payment_pending = Payment.objects.create(
            borrowing=self.borrowing,
            session_url="http://stripe.com/session/1",
            session_id="sess_1",
            session_expires_at=self.fixed_date + timedelta(hours=1),
            money_to_pay=15.00,
            status=Payment.Status.PENDING,
            type=Payment.Type.PAYMENT
        )
        self.payment_paid = Payment.objects.create(
            borrowing=self.borrowing,
            session_url="http://stripe.com/session/2",
            session_id="sess_2",
            session_expires_at=self.fixed_date + timedelta(hours=1),
            money_to_pay=15.00,
            status=Payment.Status.PAID,
            type=Payment.Type.PAYMENT
        )

    @patch('payment_service.tasks.send_telegram_message')
    def test_notify_successful_payment_success(self, mock_send_telegram):
        mock_send_telegram.return_value = True

        result = notify_successful_payment(self.payment_paid.id)

        expected_message = (
            f"Payment Successfully Completed!\n"
            f"Payment ID: {self.payment_paid.id}\n"
            f"Borrowing ID: {self.borrowing.id}\n"
            f"User: {self.user.email}\n"
            f"Book: {self.book.title}\n"
            f"Amount Paid: ${self.payment_paid.money_to_pay:.2f}\n"
            f"Type: {self.payment_paid.type}\n"
            f"Status: {self.payment_paid.status}\n"
            f"Payment Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        mock_send_telegram.assert_called_once_with(expected_message)

    @patch('payment_service.tasks.send_telegram_message')
    def test_notify_successful_payment_status_not_paid(
            self,
            mock_send_telegram
    ):
        mock_send_telegram.return_value = True
        result = notify_successful_payment(self.payment_pending.id)
        mock_send_telegram.assert_not_called()

    @patch('payment_service.tasks.send_telegram_message')
    def test_notify_successful_payment_payment_not_found(
            self,
            mock_send_telegram
    ):
        mock_send_telegram.return_value = True

        with self.assertRaises(Exception):
            notify_successful_payment(999)

    @patch('payment_service.tasks.send_telegram_message')
    def test_notify_successful_payment_send_failed(self, mock_send_telegram):
        mock_send_telegram.return_value = False

        with self.assertRaises(Exception):
            notify_successful_payment(self.payment_paid.id)

        mock_send_telegram.assert_called_once()
