from django.contrib.auth import get_user_model
from django.test import TestCase
from book_service.models import Book
from borrowing_service.models import Borrowing
from payment_service.models import Payment
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


class BaseTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            email="testuser@example.com",
            password="testpass123"
        )
        cls.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover=Book.CoverType.HARD,
            inventory=10,
            daily_fee=1.50
        )

    def setUp(self):
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=datetime.now().date(),
            expected_return_date=datetime.now().date() + timedelta(days=7)
        )
        self.payment = Payment.objects.create(
            borrowing=self.borrowing,
            session_url="https://example.com/session",
            session_id="sess_123456",
            session_expires_at=timezone.now() + timedelta(hours=24),
            money_to_pay=10.99,
            status=Payment.Status.PENDING,
            type=Payment.Type.PAYMENT
        )

    def assertNotificationMessage(
            self,
            mock_send_notification,
            expected_message
    ):
        mock_send_notification.assert_called_once()
        actual_message = mock_send_notification.call_args[0][0]
        self.assertEqual(actual_message, expected_message)
