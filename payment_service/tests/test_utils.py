import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone as datetime_timezone
from decimal import Decimal
from django.utils import timezone
from django.test import TestCase, RequestFactory
from payment_service.models import Payment
from payment_service.utils import expired_sessions, create_payment_session
import stripe


class TestUtils(TestCase):

    def setUp(self):
        """
        Initialize test data.
        """
        self.factory = RequestFactory()
        self.current_time = timezone.now()
        self.past_time = self.current_time - timedelta(days=1)
        self.future_time = self.current_time + timedelta(days=1)

    @patch("payment_service.utils.Payment.objects.filter")
    def test_expired_sessions(self, mock_filter):
        """
        Test for the expired_sessions function.
        Checks if the function correctly returns payments with expired sessions.
        """
        # Arrange
        mock_filter.return_value = MagicMock()

        # Act
        current_time, expired_payments = expired_sessions()

        # Assert
        mock_filter.assert_called_once_with(
            session_expires_at__lt=current_time, status=Payment.Status.PENDING
        )
        # Compare only the significant parts of datetime (ignoring microseconds)
        self.assertEqual(
            current_time.replace(microsecond=0),
            self.current_time.replace(microsecond=0),
        )
        self.assertIsNotNone(expired_payments)

    @patch("payment_service.utils.Payment.objects.filter")
    def test_expired_sessions_no_expired_payments(self, mock_filter):
        """
        Test for the expired_sessions function when there are no expired payments.
        """
        # Arrange
        mock_filter.return_value = Payment.objects.none()  # No expired payments

        # Act
        current_time, expired_payments = expired_sessions()

        # Assert
        mock_filter.assert_called_once_with(
            session_expires_at__lt=current_time, status=Payment.Status.PENDING
        )
        # Compare only the significant parts of datetime (ignoring microseconds)
        self.assertEqual(
            current_time.replace(microsecond=0),
            self.current_time.replace(microsecond=0),
        )
        self.assertEqual(expired_payments.count(), 0)

    @patch("payment_service.utils.create_stripe_session")
    @patch("payment_service.utils.Payment.objects.create")
    def test_create_payment_session(self, mock_create, mock_stripe_session):
        """
        Test for the create_payment_session function.
        Checks if the function correctly creates a payment session and payment.
        """
        # Arrange
        borrowing = MagicMock()
        borrowing.book.daily_fee = Decimal("10.00")
        borrowing.expected_return_date = self.current_time + timedelta(days=5)
        borrowing.borrow_date = self.current_time
        borrowing.book.title = "Test Book"
        request = self.factory.get("/fake-path/")

        # Create a datetime with timezone for comparison
        expected_expires_at = datetime.fromtimestamp(
            self.future_time.timestamp(), tz=datetime_timezone.utc
        )

        # Mock Stripe session
        mock_stripe_session.return_value = MagicMock(
            id="test_session_id",
            expires_at=self.future_time.timestamp(),
            url="http://stripe.com/session",
        )
        mock_create.return_value = MagicMock()

        # Act
        payment, session_url = create_payment_session(borrowing, request)

        # Assert
        mock_stripe_session.assert_called_once()
        mock_create.assert_called_once_with(
            borrowing=borrowing,
            status=Payment.Status.PENDING,
            type=Payment.Type.PAYMENT,
            money_to_pay=Decimal("50.00"),
            session_id="test_session_id",
            session_expires_at=expected_expires_at,  # Use datetime with timezone
            session_url="http://stripe.com/session",
        )
        self.assertIsNotNone(payment)
        self.assertEqual(session_url, "http://stripe.com/session")

    @patch("payment_service.utils.create_stripe_session")
    @patch("payment_service.utils.Payment.objects.create")
    def test_create_payment_session_fine(self, mock_create, mock_stripe_session):
        """
        Test for the create_payment_session function with payment type FINE.
        """
        # Arrange
        borrowing = MagicMock()
        borrowing.book.daily_fee = Decimal("10.00")
        borrowing.expected_return_date = self.current_time + timedelta(days=5)
        borrowing.borrow_date = self.current_time
        borrowing.actual_return_date = self.current_time + timedelta(
            days=7
        )  # Late return
        borrowing.book.title = "Test Book"
        request = self.factory.get("/fake-path/")

        # Mock Stripe session
        mock_stripe_session.return_value = MagicMock(
            id="test_session_id",
            expires_at=self.future_time.timestamp(),
            url="http://stripe.com/session",
        )
        mock_create.return_value = MagicMock()

        # Act
        payment, session_url = create_payment_session(
            borrowing, request, payment_type=Payment.Type.FINE
        )

        # Assert
        mock_stripe_session.assert_called_once()
        mock_create.assert_called_once_with(
            borrowing=borrowing,
            status=Payment.Status.PENDING,
            type=Payment.Type.FINE,
            money_to_pay=Decimal("20.00"),  # 10.00 * (7 - 5) = 20.00
            session_id="test_session_id",
            session_expires_at=datetime.fromtimestamp(
                self.future_time.timestamp(), tz=datetime_timezone.utc
            ),
            session_url="http://stripe.com/session",
        )
        self.assertIsNotNone(payment)
        self.assertEqual(session_url, "http://stripe.com/session")

    @patch("payment_service.utils.create_stripe_session")
    def test_create_payment_session_stripe_error(self, mock_stripe_session):
        """
        Test for the create_payment_session function with a Stripe error.
        """
        # Arrange
        borrowing = MagicMock()
        borrowing.book.daily_fee = Decimal("10.00")
        borrowing.expected_return_date = self.current_time + timedelta(days=5)
        borrowing.borrow_date = self.current_time
        borrowing.book.title = "Test Book"
        request = self.factory.get("/fake-path/")

        # Mock Stripe exception
        mock_stripe_session.side_effect = stripe.error.StripeError("Stripe error")

        # Act & Assert
        with self.assertRaises(stripe.error.StripeError):
            create_payment_session(borrowing, request)

    def test_create_payment_session_invalid_payment_type(self):
        """
        Test for the create_payment_session function with an invalid payment type.
        """
        # Arrange
        borrowing = MagicMock()
        request = self.factory.get("/fake-path/")

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            create_payment_session(borrowing, request, payment_type="INVALID_TYPE")
        self.assertEqual(str(context.exception), "Invalid payment type: INVALID_TYPE")

    @patch("payment_service.utils.create_stripe_session")
    @patch("payment_service.utils.Payment.objects.create")
    def test_create_payment_session_zero_amount(self, mock_create, mock_stripe_session):
        """
        Test for the create_payment_session function with a zero payment amount.
        """
        # Arrange
        borrowing = MagicMock()
        borrowing.book.daily_fee = Decimal("0.00")  # Zero amount
        borrowing.expected_return_date = self.current_time + timedelta(days=5)
        borrowing.borrow_date = self.current_time
        borrowing.book.title = "Test Book"
        request = self.factory.get("/fake-path/")

        # Mock Stripe session
        mock_stripe_session.return_value = MagicMock(
            id="test_session_id",
            expires_at=self.future_time.timestamp(),
            url="http://stripe.com/session",
        )
        mock_create.return_value = MagicMock()

        # Act
        payment, session_url = create_payment_session(borrowing, request)

        # Assert
        mock_stripe_session.assert_called_once()
        mock_create.assert_called_once_with(
            borrowing=borrowing,
            status=Payment.Status.PENDING,
            type=Payment.Type.PAYMENT,
            money_to_pay=Decimal("0.00"),  # Zero amount
            session_id="test_session_id",
            session_expires_at=datetime.fromtimestamp(
                self.future_time.timestamp(), tz=datetime_timezone.utc
            ),
            session_url="http://stripe.com/session",
        )
        self.assertIsNotNone(payment)
        self.assertEqual(session_url, "http://stripe.com/session")


if __name__ == "__main__":
    unittest.main()
