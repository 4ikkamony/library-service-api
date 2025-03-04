from django.contrib.auth import get_user_model
from django.test import TestCase
from unittest.mock import patch, Mock
from borrowing_service.tasks import notify_new_borrowing, check_overdue_borrowings
from borrowing_service.models import Borrowing
from book_service.models import Book
import datetime

User = get_user_model()


class NotifyNewBorrowingTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            email="testuser@example.com", password="testpass123"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover=Book.CoverType.HARD,
            inventory=10,
            daily_fee=1.50,
        )
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=datetime.date.today(),
            expected_return_date=datetime.date.today() + datetime.timedelta(days=7),
        )

        self.mock_send_telegram = Mock(return_value=True)
        self.patcher_send_telegram = patch(
            "borrowing_service.tasks.send_telegram_message", new=self.mock_send_telegram
        )
        self.patcher_send_telegram.start()

    def tearDown(self):
        if hasattr(self, "patcher_send_telegram"):
            self.patcher_send_telegram.stop()

    def test_notify_new_borrowing_success(self):
        try:
            result = notify_new_borrowing(self.borrowing.id)
        except Exception as e:
            self.fail(f"Function raised unexpected exception: {str(e)}")

        self.assertIsNone(result)

        expected_message = (
            "New Borrowing Created!\n"
            f"Borrowing ID: {self.borrowing.id}\n"
            "User: testuser@example.com\n"
            "Book: Test Book\n"
            f"Borrow Date: {datetime.date.today()}\n"
            f"Expected Return Date: {datetime.date.today() + datetime.timedelta(days=7)}"
        )
        self.mock_send_telegram.assert_called_once_with(expected_message)

    def test_notify_new_borrowing_not_found(self):
        non_existent_id = 999

        with self.assertRaises(Exception) as context:
            notify_new_borrowing(non_existent_id)

        self.assertEqual(
            str(context.exception), f"Borrowing with ID {non_existent_id} not found"
        )

        self.mock_send_telegram.assert_not_called()

    def test_notify_new_borrowing_send_telegram_fails(self):
        self.mock_send_telegram.return_value = False

        with self.assertRaises(Exception) as context:
            notify_new_borrowing(self.borrowing.id)

        self.assertEqual(str(context.exception), "Failed to send Telegram notification")
        self.mock_send_telegram.assert_called_once()

    def test_notify_new_borrowing_unexpected_error(self):
        with patch(
            "borrowing_service.tasks.Borrowing.objects.get",
            side_effect=Exception("Unexpected error"),
        ):
            with self.assertRaises(Exception) as context:
                notify_new_borrowing(self.borrowing.id)

            self.assertEqual(str(context.exception), "Unexpected error")

        self.mock_send_telegram.assert_not_called()


class CheckOverdueBorrowingsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            email="testuser@example.com", password="testpass123"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover=Book.CoverType.HARD,
            inventory=10,
            daily_fee=1.50,
        )

        self.mock_send_telegram = Mock(return_value=True)
        self.patcher_send_telegram = patch(
            "borrowing_service.tasks.send_telegram_message", new=self.mock_send_telegram
        )
        self.patcher_send_telegram.start()

        self.patcher_today_overdue = patch(
            "borrowing_service.tasks.today_overdue_borrowings"
        )
        self.mock_today_overdue = self.patcher_today_overdue.start()

    def tearDown(self):
        self.patcher_send_telegram.stop()
        self.patcher_today_overdue.stop()

    def test_check_overdue_borrowings_no_overdue(self):
        self.mock_today_overdue.return_value = (
            datetime.date.today(),
            Borrowing.objects.none(),
        )

        try:
            result = check_overdue_borrowings()
        except Exception as e:
            self.fail(f"Function raised unexpected exception: {str(e)}")

        self.assertIsNone(result)
        self.mock_send_telegram.assert_called_once_with("No borrowings overdue today!")

    def test_check_overdue_borrowings_send_telegram_fails(self):
        self.mock_send_telegram.return_value = False
        self.mock_today_overdue.return_value = (
            datetime.date.today(),
            Borrowing.objects.none(),
        )

        with self.assertRaises(Exception) as context:
            check_overdue_borrowings()

        self.assertEqual(str(context.exception), "Failed to send Telegram notification")
        self.mock_send_telegram.assert_called_once_with("No borrowings overdue today!")

    def test_check_overdue_borrowings_unexpected_error(self):
        self.mock_today_overdue.side_effect = Exception("Unexpected error")

        with self.assertRaises(Exception) as context:
            check_overdue_borrowings()

        self.assertEqual(str(context.exception), "Unexpected error")
        self.mock_send_telegram.assert_not_called()
